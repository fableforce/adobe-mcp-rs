"""Run a bounded live phase against isolated broker configuration.

Document fixtures are supplied explicitly by the caller. Never installs plugins,
changes security settings, retries a mutation, or closes Adobe applications.
"""
import argparse
import importlib.util
import json
import pathlib
import socket
import subprocess
import time

spec = importlib.util.spec_from_file_location("verify_mcp", pathlib.Path(__file__).with_name("verify-mcp.py"))
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=transport.HOSTS, required=True)
    parser.add_argument("--binaries", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--script", type=pathlib.Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--tool")
    parser.add_argument("--arguments", default="{}")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--expected-output", action="append", default=[])
    parser.add_argument("--no-undo-group", action="store_true", help="Disable the optional AE undo group for project/export lifecycle calls")
    args = parser.parse_args()
    prefix = transport.HOSTS[args.host][0]
    binary = args.binaries.resolve() / (prefix + "-mcp.exe")
    config = args.output / (args.host + ".toml")
    import tomllib
    port = int(tomllib.loads(config.read_text(encoding="utf-8-sig"))["daemon_addr"].split(":")[-1])
    with (args.output / (args.host + "-daemon.stderr.log")).open("a", encoding="utf-8") as log:
        daemon = subprocess.Popen([str(binary), "--config", str(config), "serve-daemon"],
                                  stdout=subprocess.DEVNULL, stderr=log,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        client = None
        try:
            deadline = time.monotonic() + 10
            while True:
                if daemon.poll() is not None:
                    raise RuntimeError("Validation daemon exited; inspect its stderr")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    if time.monotonic() > deadline:
                        raise
                    time.sleep(0.1)
            client = transport.Client(binary, args.output / (args.host + "-mcp.stderr.log"), config)
            if args.script:
                arguments = {"code": args.script.read_text(encoding="utf-8"), "mode": "unsafe",
                             "description": args.label, "timeoutMs": args.timeout_ms,
                             "expectedOutputPaths": args.expected_output}
                if args.no_undo_group:
                    arguments["undoGroup"] = False
                response = client.tool("run-jsx" if args.host == "aftereffects" else "run-script", arguments,
                                       args.timeout_ms / 1000 + 15)
            else:
                response = client.tool(args.tool or transport.HOSTS[args.host][1], json.loads(args.arguments),
                                       args.timeout_ms / 1000 + 15)
            data = transport.payload(response)
            (args.output / (args.host + "-" + args.label + ".json")).write_text(json.dumps(response, indent=2), encoding="utf-8")
            result = data.get("result", {}) if isinstance(data, dict) else data
            if isinstance(result, dict):
                result = {k: v for k, v in result.items() if not k.startswith("_")}
            print(json.dumps({"host": args.host, "label": args.label, "state": data.get("state"),
                              "requestId": data.get("requestId"), "message": data.get("message"),
                              "isError": response.get("result", {}).get("isError", False), "result": result})[:2400], flush=True)
        finally:
            if client:
                client.close()
            daemon.terminate()
            daemon.wait(timeout=10)


if __name__ == "__main__":
    main()
