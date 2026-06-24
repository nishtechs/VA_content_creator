const path = require('path');
const { pathToFileURL } = require('url');

// The first argument is the absolute path to the actual MCP server script
const targetScript = path.resolve(process.argv[2]);

// Redirect console.log to stderr so it doesn't corrupt stdout which is reserved for JSON-RPC
const originalConsoleLog = console.log;
console.log = function() {
    process.stderr.write(Array.from(arguments).join(' ') + '\n');
};

console.info = function() {
    process.stderr.write(Array.from(arguments).join(' ') + '\n');
};
console.warn = function() {
    process.stderr.write(Array.from(arguments).join(' ') + '\n');
};

// Now load the target script dynamically to support both CJS and ESM (.mjs)
(async () => {
    try {
        await import(pathToFileURL(targetScript).href);
    } catch (err) {
        if (err.code === 'ERR_REQUIRE_ESM' || err.code === 'ERR_MODULE_NOT_FOUND') {
            process.stderr.write("Import error: " + err + "\n");
        } else {
            // Fallback for older modules or specific CJS edge cases if needed
            require(targetScript);
        }
    }
})();
