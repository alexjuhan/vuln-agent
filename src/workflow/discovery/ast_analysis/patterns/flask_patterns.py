# Common patterns for Flask applications
SOURCE_PATTERNS = {
    'request.form', 'request.args', 'request.get_json', 
    'request.data', 'request.values', 'request.files',
    'request.headers', 'request.cookies', 'request.environ'
}

SINK_PATTERNS = {
    'make_response', 'jsonify', 'render_template', 
    'send_file', 'send_from_directory', 'Response', 
    'redirect', 'abort', 'stream_with_context'
}

PROCESSOR_PATTERNS = {
    'before_request', 'after_request', 
    'before_first_request', 'teardown_request',
    'preprocess_request', 'process_response'
}

TRUST_BOUNDARIES = {
    'wsgi': {
        'name': "WSGI Boundary",
        'entry_points': {"wsgi_app"},
        'exit_points': {"__call__"},
        'sanitizers': set()
    },
    'request_processing': {
        'name': "Request Processing",
        'entry_points': PROCESSOR_PATTERNS,
        'exit_points': SINK_PATTERNS,
        'sanitizers': {'escape', 'safe_join', 'secure_filename'}
    },
    'session': {
        'name': "Session Boundary",
        'entry_points': {'session'},
        'exit_points': {'session.save'},
        'sanitizers': {'session.sign', 'session.encrypt'}
    }
} 