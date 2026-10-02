from app.bot.handlers import setup_dispatcher


def test_setup_dispatcher():
    dp = setup_dispatcher()
    assert dp is not None
    router_names = [r.name for r in dp.sub_routers]
    assert "start" in router_names
    assert "help" in router_names
    assert "status" in router_names
    assert "cancel" in router_names
    assert "about" in router_names
    assert "admin" in router_names
    assert "document" in router_names
