import { execFile } from "node:child_process";
import { createReadStream, existsSync, statSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { extname, join } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL(".", import.meta.url));
const port = Number(process.env.ZAVOD_PORT || 4173);
const run = promisify(execFile);
const maxUploadBytes = 30 * 1024 * 1024;
const bundledPython = "/Users/apple/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const python = process.env.ZAVOD_PYTHON || (existsSync(bundledPython) ? bundledPython : "python3");
const allowedHosts = new Set([`localhost:${port}`, `127.0.0.1:${port}`, `[::1]:${port}`]);
const allowedOrigins = new Set([`http://localhost:${port}`, `http://127.0.0.1:${port}`, `http://[::1]:${port}`]);
let pdfBusy = false;
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json; charset=utf-8"
};
const publicFiles = new Set(["index.html", "styles.css", "app.js"]);
const securityHeaders = {
  "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY"
};

function sendJson(response, status, value) {
  response.writeHead(status, { ...securityHeaders, "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  response.end(JSON.stringify(value));
}

async function readJson(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > maxUploadBytes * 1.4) throw new Error("FILE_TOO_LARGE");
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

async function extractPdf(request, response) {
  let workDir;
  try {
    const payload = await readJson(request);
    const buffer = Buffer.from(payload.data || "", "base64");
    if (!buffer.length || buffer.length > maxUploadBytes) return sendJson(response, 413, { error: "FILE_TOO_LARGE" });
    if (buffer.subarray(0, 5).toString() !== "%PDF-") return sendJson(response, 400, { error: "NOT_A_PDF" });

    workDir = await mkdtemp(join(tmpdir(), "zavod-pdf-"));
    const inputPath = join(workDir, "input.pdf");
    await writeFile(inputPath, buffer, { mode: 0o600 });
    const { stdout } = await run(python, [join(root, "pdf_extract.py"), inputPath], { maxBuffer: 24 * 1024 * 1024, timeout: 45000 });
    return sendJson(response, 200, JSON.parse(stdout));
  } catch (error) {
    const message = error?.message === "FILE_TOO_LARGE" ? "FILE_TOO_LARGE" : "PDF_EXTRACTION_FAILED";
    return sendJson(response, message === "FILE_TOO_LARGE" ? 413 : 422, { error: message });
  } finally {
    if (workDir) await rm(workDir, { recursive: true, force: true }).catch(() => {});
  }
}

await mkdir(root, { recursive: true });
createServer(async (request, response) => {
  const remote = request.socket.remoteAddress || "";
  const isLoopback = remote === "127.0.0.1" || remote === "::1" || remote.endsWith(":127.0.0.1");
  if (!isLoopback) return sendJson(response, 403, { error: "LOCAL_ONLY" });
  const host = request.headers.host || "";
  if (!allowedHosts.has(host)) return sendJson(response, 403, { error: "INVALID_HOST" });
  const url = new URL(request.url, `http://${host}`);
  if (request.method === "POST" && url.pathname === "/api/extract-pdf") {
    const origin = request.headers.origin;
    if (origin && !allowedOrigins.has(origin)) return sendJson(response, 403, { error: "INVALID_ORIGIN" });
    if (!String(request.headers["content-type"] || "").toLowerCase().startsWith("application/json")) return sendJson(response, 415, { error: "JSON_REQUIRED" });
    if (pdfBusy) return sendJson(response, 429, { error: "PDF_BUSY" });
    pdfBusy = true;
    try { return await extractPdf(request, response); }
    finally { pdfBusy = false; }
  }
  if (request.method !== "GET" && request.method !== "HEAD") return sendJson(response, 405, { error: "METHOD_NOT_ALLOWED" });

  let requested;
  try { requested = url.pathname === "/" ? "index.html" : decodeURIComponent(url.pathname).replace(/^\/+/, ""); }
  catch { requested = ""; }
  if (!publicFiles.has(requested)) {
    response.writeHead(404, { ...securityHeaders, "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
    return;
  }
  const filePath = join(root, requested);
  if (!existsSync(filePath) || !statSync(filePath).isFile()) return sendJson(response, 404, { error: "NOT_FOUND" });
  response.writeHead(200, { ...securityHeaders, "Content-Type": types[extname(filePath)] || "application/octet-stream", "Cache-Control": "no-store" });
  if (request.method === "HEAD") return response.end();
  createReadStream(filePath).pipe(response);
}).listen(port, "127.0.0.1", () => console.log(`ZAVOD → http://localhost:${port}`));
