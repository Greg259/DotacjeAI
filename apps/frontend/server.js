const http = require("http");

const page = `<!doctype html>
<html lang="pl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>DotacjeAI</title></head>
<body style="font-family:system-ui;max-width:720px;margin:64px auto;padding:0 24px">
  <h1>DotacjeAI</h1>
  <p>Środowisko MVP działa. Docelowy frontend Next.js zostanie wdrożony w kolejnym etapie.</p>
</body>
</html>`;

const server = http.createServer((request, response) => {
  if (request.url === "/health") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ status: "ok", service: "frontend" }));
    return;
  }
  response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
  response.end(page);
});

server.listen(3000, "0.0.0.0");
