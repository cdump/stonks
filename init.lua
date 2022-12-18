--
-- stonks module for Awesome WM
--
-- GitHub: https://github.com/cdump/stonks
--
-- Add to rc.lua:
-- local stonks = require("stonks")
-- ..
-- stonks.addToWidget(widget, update_fcn, config)
--
-- Example:
-- stonks.addToWidget(widgets.quotes.widget, widgets.quotes.update, {
--	{"moex_currency", "EUR_RUB__TOM", "€" },
--	{"moex_currency", "USD000UTSTOM", "$" },
--	{"binance", "BTCUSDT", "₿" }
-- })
--

local awful = require("awful")
local naughty = require("naughty")
local capi = {
    mouse = mouse,
    screen = screen
}

local function addToWidget(mywidget, update_text, tickers)
    local tooltip_text = 'none'

    local dirname = require('debug').getinfo(1).source:match("@?(.*/)")
    local cmd = dirname .. '/stonks.py --format awesome'
    for _, v in pairs(tickers) do
        assert(#v == 3)
        cmd = cmd .. ' --ticker="' .. v[1] .. ':' .. v[2] .. ':' .. v[3] .. '"'
    end

    awful.spawn.with_line_callback(cmd, {
        stdout = function(line)
            local _, _, key, value = string.find(line, "(%a+)%s*(.*)")
            if key == 'tooltipstart' then
                tooltip_text = ''
            elseif key == 'tooltip' then
                tooltip_text = tooltip_text .. value .. '\n'
            elseif key == 'text' then
                update_text(value)
            end
        end,
    })

    local tooltip = nil
    mywidget:connect_signal('mouse::enter', function()
        tooltip = naughty.notify({
            text = "<span font_desc='monospace'>" .. tooltip_text .. "</span>",
            position = "bottom_right",
            timeout = 0,
            hover_timeout = 0.5,
            screen = capi.mouse.screen
        })
    end)
    mywidget:connect_signal('mouse::leave', function() naughty.destroy(tooltip) end)
end

return {
    addToWidget = addToWidget,
}
