# stonks

Stocks widget for [Awesome WM](https://awesomewm.org/) and [WayBar](https://github.com/Alexays/Waybar) ([Sway WM](https://swaywm.org/))

## HowTo

### Awesome WM
```sh
$ cd ~/.config/awesome/
$ git clone --depth 1 https://github.com/cdump/stonks
$ cd stonks && poetry install  # https://python-poetry.org/docs/#installation
$ vim rc.lua

# local stonks = require("stonks")
# ..
# stonks.addToWidget(widget, update_fcn, config)
#
# Example:
# stonks.addToWidget(widgets.quotes.widget, widgets.quotes.update, {
#	{"moex_currency", "EUR_RUB__TOM", "€" },
#	{"moex_currency", "USD000UTSTOM", "$" },
#	{"binance", "BTCUSDT", "₿" }
# })
```
