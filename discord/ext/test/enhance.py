def embed_eq(embed1, embed2):
    # fields = ['title', 'description']
    # return all([getattr(embed1, f, None) == getattr(embed2, f, None)
    #             for f in fields])

    return all([embed1.title == embed2.title,
                embed1.description == embed2.description,
                embed1.url == embed2.url,
                embed1.footer.text == embed2.footer.text,
                embed1.image.url == embed2.image.url])


def embed_proxy_eq(embed_proxy1, embed_proxy2):
    return embed_proxy1.__repr__ == embed_proxy2.__repr__
