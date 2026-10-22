// Run using run-script with undoGroup:false and a fresh expectedOutputPaths
// entry. args.compName / args.outputDirectory / args.templateName are required.
// Select only an isolated test project or a project explicitly authorized by
// the user. This recipe does not close/restart the app or retry export.
(function (options) {
    if (!app.project.file) throw new Error("Save the authorized project first");
    if (!options.compName || !options.outputDirectory || !options.templateName) {
        throw new Error("compName, outputDirectory and templateName are required");
    }
    var comp = null;
    for (var i = 1; i <= app.project.numItems; i++) {
        var item = app.project.item(i);
        if (item instanceof CompItem && item.name === options.compName) {
            if (comp) throw new Error("Composition name is ambiguous");
            comp = item;
        }
    }
    if (!comp) throw new Error("Composition not found");
    var directory = new Folder(options.outputDirectory);
    if (!directory.exists) throw new Error("Output directory must exist");
    var output = new File(directory.fsName + "/" + options.templateName + ".mogrt");
    if (output.exists) throw new Error("Refusing an existing output file");
    comp.motionGraphicsTemplateName = options.templateName;
    // Save all controller/name changes before export to avoid a save prompt.
    app.project.save();
    var outputPath = output.fsName;
    var exported = comp.exportAsMotionGraphicsTemplate(false, directory.fsName);
    // Do not dereference cached comp/layer/property objects after export.
    if (!exported) throw new Error("After Effects declined MOGRT export");
    return { exported: exported, outputPath: outputPath };
})(args);
