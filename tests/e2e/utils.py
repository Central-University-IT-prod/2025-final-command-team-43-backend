def empty(response):
    if len(response.json()) != 0:
        raise AssertionError("The response list is not empty")
