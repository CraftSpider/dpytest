from typing import List
import sys

def embed_eq(embed1, embed2, full=False, attrs=None):
    if embed1 == embed2:
        return True
    if embed1 is None and embed2 is not None:
        return False
    if embed2 is None and embed1 is not None:
        return False


    embed1_data = embed1.to_dict()
    embed2_data = embed2.to_dict()

    if full:
        return embed1_data == embed2_data
    elif attrs is not None:
        attr_comp = []
        for attr in attrs:
            try:
                if isinstance(attr, List):
                    # Since an iterable was passed, assume its to compare subelements of a proxy field
                    value1 = embed1_data
                    value2 = embed2_data
                    for subattr in attr:
                        value1 = value1.get(subattr, None)
                        value2 = value2.get(subattr, None)
                        if value1 is None or value2 is None:
                            break
                    attr_comp.append(value1 == value2)
                else:
                    attr_comp.append(embed1_data.get(attr, None) == embed2_data.get(attr, None))
            except KeyError:
                attr_comp.append(False)

        return all(attr_comp)
    else:
        return all([embed1.title == embed2.title,
                    embed1.description == embed2.description,
                    embed1.url == embed2.url,
                    embed1.footer.text == embed2.footer.text,
                    embed1.image.url == embed2.image.url])


def embed_proxy_eq(embed_proxy1, embed_proxy2):
    return embed_proxy1.__repr__ == embed_proxy2.__repr__


def compare_dicts(got, exp) -> str:
    try:
        import difflib
        import pprint
        return 'Diff:\n' + '\n'.join(difflib.ndiff(pprint.pformat(got).splitlines(), pprint.pformat(exp).splitlines()))
    except ImportError:
        return f"Got:\n{got}\nExpected:\n{exp}"
