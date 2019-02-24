def log_error(logger, response, title):
    logger.error(
        "[{}] {}, {}, {}\n".format(
            title,
            response.status,
            response.body.get('errorCode') or response.body.get('errorMessage'),
            response.body.get('errorMessage'),
        )
    )
