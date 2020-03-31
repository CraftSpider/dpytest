
def embed_eq(embed1, embed2):
    if embed1 == embed2:
        return True
    if embed1 is None and embed2 is not None:
        return False
    if embed2 is None and embed1 is not None:
        return False

    return all([embed1.title == embed2.title,
                embed1.description == embed2.description,
                embed1.url == embed2.url,
                embed1.footer.text == embed2.footer.text,
                embed1.image.url == embed2.image.url])


def embed_proxy_eq(embed_proxy1, embed_proxy2):
    return embed_proxy1.__repr__ == embed_proxy2.__repr__
