def create_log_line(file_id, hit):
    time = "1496925214.544"
    ip = "192.168.10." + file_id
    size = "1000"
    method = "GET"
    url = "http://192.168.10." + file_id + "/1.html"
    source = "ORIGINAL_DST/192.168.10." + file_id
    content_type = "text/html"

    line_parts = ([time, file_id, ip, "TCP_HIT/200" if hit else "TCP_MISS/200", size, method, url, '-', source,
                   content_type, '\n'])
    return ' '.join(line_parts)


def create_log_file(file_path):

    with open(file_path, "w+") as f:
        f.write(create_log_line("1", True))
        f.write(create_log_line("2", False))
        f.write(create_log_line("3", False))
        f.write(create_log_line("2", True))
        f.write(create_log_line("3", False))
        f.write(create_log_line("4", False))
        f.write(create_log_line("3", False))
        f.write(create_log_line("5", True))


def append_log_file(file_path):

    with open(file_path, "a+") as f:
        f.write(create_log_line("1", True))
        f.write(create_log_line("2", False))
        f.write(create_log_line("3", False))
        f.write(create_log_line("4", False))
        f.write(create_log_line("2", True))
        f.write(create_log_line("4", False))
        f.write(create_log_line("5", True))
