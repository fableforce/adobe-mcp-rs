"""Bounded stdio MCP checks. Writes evidence only to the explicit output directory.

Uses the repository's existing JSON-lines transport and host binaries; does not
install bridges, alter preferences, or open/close Adobe documents.
"""
import argparse
import json
import pathlib
import queue
import subprocess
import threading

HOSTS = {
    "aftereffects": ("ae", "list-ae-instances"),
    "illustrator": ("ai", "list-illustrator-instances"),
    "indesign": ("id", "list-indesign-instances"),
    "photoshop": ("ps", "list-photoshop-instances"),
    "premiere": ("pr", "list-premiere-instances"),
}


class Client:
    def __init__(self, binary, log, config=None):
        self.log = log.open("a", encoding="utf-8")
        command = [str(binary)] + (["--config", str(config)] if config else []) + ["serve-stdio"]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.log,
                                        text=True, encoding="utf-8")
        self.responses = queue.Queue()
        self.sequence = 0
        def read():
            for line in self.process.stdout:
                try:
                    self.responses.put(json.loads(line))
                except ValueError:
                    self.responses.put({"transportError": "Non-JSON stdout", "line": line})
            self.responses.put({"transportError": "MCP process exited"})
        threading.Thread(target=read, daemon=True).start()
        self.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                "clientInfo": {"name": "adobe-fork-verification", "version": "1"}})
        self.send({"method": "notifications/initialized"})

    def send(self, request):
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", **request}) + "\n")
        self.process.stdin.flush()

    def call(self, method, params=None, timeout=150):
        self.sequence += 1
        self.send({"id": self.sequence, "method": method, "params": params or {}})
        while True:
            response = self.responses.get(timeout=timeout)
            if "transportError" in response:
                raise RuntimeError(response)
            if response.get("id") == self.sequence:
                return response

    def tool(self, name, arguments=None, timeout=150):
        return self.call("tools/call", {"name": name, "arguments": arguments or {}}, timeout)

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)
        self.process.stdout.close()
        self.log.close()


def payload(response):
    result = response.get("result", {})
    for item in result.get("content", []):
        if item.get("type") == "text":
            try:
                return json.loads(item["text"])
            except ValueError:
                pass
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binaries", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--host", choices=HOSTS)
    parser.add_argument("--config", type=pathlib.Path)
    parser.add_argument("--script", type=pathlib.Path)
    parser.add_argument("--tool")
    parser.add_argument("--arguments", default="{}")
    parser.add_argument("--label", default="probe")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for host in ([args.host] if args.host else HOSTS):
        prefix, listing = HOSTS[host]
        client = Client(args.binaries / (prefix + "-mcp.exe"), args.output / (host + ".stderr.log"), args.config)
        try:
            if args.script:
                result = client.tool("run-jsx" if host == "aftereffects" else "run-script", {
                    "code": args.script.read_text(encoding="utf-8"), "mode": "unsafe",
                    "description": args.label, "timeoutMs": args.timeout_ms,
                }, args.timeout_ms / 1000 + 15)
            elif args.tool:
                result = client.tool(args.tool, json.loads(args.arguments), args.timeout_ms / 1000 + 15)
            else:
                result = {"tools": client.call("tools/list"), "instances": client.tool(listing),
                          "bridge": client.tool("run-bridge-test")}
            (args.output / (host + "-" + args.label + ".json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
            if args.script or args.tool:
                print(host, json.dumps(payload(result))[:1600], "isError=", result.get("result", {}).get("isError", False), flush=True)
            else:
                print(host, "instances=", json.dumps(payload(result["instances"]))[:600],
                      "bridge=", json.dumps(payload(result["bridge"]))[:400], flush=True)
        finally:
            client.close()


if __name__ == "__main__":
    main()
