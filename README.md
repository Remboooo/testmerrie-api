# Testmerrie API

## What?
This is Python WSGI middleware for authenticating and dispatching media from OvenMediaEngine to the [testmerrie-react](https://github.com/Remboooo/testmerrie-react) React frontend. Features:
 - Discord authentication
 - I made dis
 - Includes Sprong, which is a homemade Python lib that completely does not resemble the Spring Java library. Really.
 - Did Python not feel enterprisey enough? Introducing Python Beans. You never knew you wanted them, but now that you know them you can call yourself a consultant and drive a fancy car and wear nice suits.

## Things to configure
 - This app needs OvenMediaEngine to do anything useful. See [OME-Server.xml.example](OME-Server.xml.example)
 - This app needs to be hosted through WSGI. See [nginx-example.txt](nginx-example.txt), [uwsgi.ini.example](uwsgi.ini.example)
 - Copy [config.yaml.example](config.yaml.example) to `config.yaml` and fill everything in

## Disclaimer
Assume I was drunk throughout building this whole thing. Reasons:
 - I probably was
 - It's just for funsies and not for professional use
 - I tried to build this while trying to implement some new concepts (dependency injection, decorator-based routing) myself, in stead of relying on external libs. You really don't want to use this in production. Ever.

## Is it finished?
No. See [TODO.md](TODO.md).

## Can I use it?
Sure, if you really want to. See [LICENSE.md](LICENSE.md).
