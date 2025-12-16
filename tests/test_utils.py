from copy import deepcopy
import pytest
from discord import Embed
from discord.ext.test.utils import embed_eq


@pytest.mark.asyncio
async def test_embed_eq_direct(bot) -> None:
    embed_1: Embed = Embed()
    embed_2: Embed = Embed()
    assert embed_eq(embed_1, embed_2) is True


@pytest.mark.asyncio
async def test_embed_eq_embed1_is_none(bot) -> None:
    embed_2: Embed = Embed()
    assert embed_eq(None, embed_2) is False


@pytest.mark.asyncio
async def test_embed_eq_embed2_is_none(bot) -> None:
    embed_1: Embed = Embed()
    assert embed_eq(embed_1, None) is False


@pytest.mark.asyncio
async def test_embed_eq_attr_title(bot) -> None:
    embed_1: Embed = Embed(title="Foo")
    embed_2: Embed = Embed(title="Bar")
    assert embed_eq(embed_1, embed_2) is False


@pytest.mark.asyncio
async def test_embed_eq_attr_description(bot) -> None:
    embed_1: Embed = Embed(title="Foo", description="This is a Foo.")
    embed_2: Embed = Embed(title="Foo", description="This is a slightly different Foo.")
    assert embed_eq(embed_1, embed_2) is False


@pytest.mark.asyncio
async def test_embed_eq_attr_url(bot) -> None:
    embed_1: Embed = Embed(title="Foo", description="This is a Foo.", url="http://www.foo.foo")
    embed_2: Embed = Embed(title="Foo", description="This is a Foo.", url="http://www.foo.bar")
    assert embed_eq(embed_1, embed_2) is False


@pytest.mark.asyncio
async def test_embed_eq_attr_footer(bot) -> None:
    embed_1: Embed = Embed(title="Foo", description="This is a Foo.", url="http://www.foo.foo")
    embed_1.set_footer(text="This is the footer for Foo.")
    embed_2: Embed = deepcopy(embed_1)
    embed_2.set_footer(text="This is a slightly different footer for Foo.")
    assert embed_eq(embed_1, embed_2) is False


@pytest.mark.asyncio
async def test_embed_eq_attr_image(bot) -> None:
    embed_1: Embed = Embed(title="Foo", description="This is a Foo.", url="http://www.foo.foo")
    embed_1.set_footer(text="This is the footer for Foo.")
    embed_1.set_image(url="http://image.foo")
    embed_2: Embed = deepcopy(embed_1)
    embed_2.set_image(url="http://image.bar")
    assert embed_eq(embed_1, embed_2) is False


@pytest.mark.asyncio
async def test_embed_eq_attr_fields(bot) -> None:
    embed_1: Embed = Embed(title="Foo", description="This is a Foo.", url="http://www.foo.foo")
    embed_1.set_footer(text="This is the footer for Foo.")
    embed_1.set_image(url="http://image.foo")
    embed_1.add_field(name="Foo", value="Foo")
    embed_2: Embed = deepcopy(embed_1)
    embed_2.add_field(name="Foo", value="Bar")
    assert embed_eq(embed_1, embed_2) is False


@pytest.mark.asyncio
async def test_embed_eq_attr_equal(bot) -> None:
    embed_1: Embed = Embed(title="Foo", description="This is a Foo.", url="http://www.foo.foo")
    embed_1.set_footer(text="This is the footer for Foo.")
    embed_1.set_image(url="http://image.foo")
    embed_1.add_field(name="Foo", value="Foo")
    embed_2: Embed = deepcopy(embed_1)
    assert embed_eq(embed_1, embed_2) is True
