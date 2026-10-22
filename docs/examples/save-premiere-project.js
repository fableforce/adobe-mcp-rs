// Windows UXP recipe for run-script. Supply input.expectedProjectPath exactly
// as reported by the app, input.outputPath as a fresh native Windows path, and
// the same output path in the tool's expectedOutputPaths array.
// A caller timeout is not permission to run this script again: recover its ID.
const project = await ppro.Project.getActiveProject();
if (!project || project.path !== args.expectedProjectPath) {
  throw new Error("Active project differs from the explicitly selected project");
}
if (typeof args.outputPath !== "string" || !/^[A-Za-z]:\\/.test(args.outputPath)) {
  throw new Error("outputPath must be a native absolute Windows path");
}
const saved = await project.saveAs(args.outputPath);
if (saved !== true) {
  throw new Error("Premiere declined or cancelled saveAs; persistence is unverified");
}
// saveAs updates the project in place. Reacquire subsequent project/sequence/
// track handles; do not treat pre-save timeline visibility as disk persistence.
const active = await ppro.Project.getActiveProject();
return { saved: true, path: active.path };
