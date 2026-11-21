---
title: Store POS
kind: open_source
year: 2025
summary: A point of sale for small shops, as a desktop app.
tags: [python, flet, sqlmodel, sqlite]
repo: https://github.com/oornnery/Store-POS
updated: 2025-12-22
---

A desktop point of sale for a small shop, from the checkout to the end of the day.

## What it does

At the checkout you search products, build the cart, put an order on hold and resume it later, and take cash, credit
(with installments), debit or PIX, linking the sale to a customer if you want. The cash register has opening,
closing, cash drops and the history of each session.

The dashboard shows sales, low stock and recent transactions, with a 7-day sales chart and sales by payment method for
any date range. Stock has products, categories, CSV import and a minimum level per product. There are Admin and
Cashier users, the company's details on receipts, light and dark themes, and English and Portuguese.

## How it is built

Python with Flet, which draws the interface with Flutter. Each screen is a view; the rules for sales, cash, stock and
login live in services; the data is SQLite through SQLModel. Passwords are hashed with bcrypt.
