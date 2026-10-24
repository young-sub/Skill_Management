const fs = require("node:fs");
const path = require("node:path");
const mkdir = fs.promises.mkdir.bind(fs.promises);
const linkedViteTemp = path.join(path.resolve(process.cwd(), "node_modules"), ".vite-temp");
fs.promises.mkdir = (target, options) => {
  if (typeof target === "string" && path.resolve(target) === linkedViteTemp) {
    const error = new Error("Avoid writing Vite config bundles through the source node_modules junction");
    error.code = "EACCES";
    return Promise.reject(error);
  }
  return mkdir(target, options);
};