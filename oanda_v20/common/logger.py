def log_error(logger, response, title):
    logger.error(
        "[{}] {}, {}, {}\n".format(
            title,
            response.status,
            response.body['errorCode'],
            response.body['errorMessage'],
        )
    )
