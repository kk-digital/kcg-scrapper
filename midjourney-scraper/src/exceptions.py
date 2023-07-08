class ScraperError(Exception):
    pass


class PlaywrightHTTTPError(ScraperError):
    """An HTTP error occurred loading a page."""
