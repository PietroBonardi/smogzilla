def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [b"Smogzilla is alive!"]