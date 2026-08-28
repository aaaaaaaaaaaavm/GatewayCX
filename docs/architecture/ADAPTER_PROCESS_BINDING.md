# GX-A1 reference process binding

## Purpose

GX-A1 began as a Python method surface. S018 moves that surface across a real process boundary so
the service plane and a bearer adapter no longer have to share memory, imports or a failure domain.

The current binding uses one JSON object per connection over TCP loopback. It is deliberately
small enough for an independently written adapter to reproduce, but it is still a reference test
binding rather than a standard.

## Envelope

Requests carry:

- `request_id`, unique at the client;
- `operation`, one of the declared GX-A1 operations; and
- `arguments`, an operation-specific object.

Responses echo the request identifier and carry `rpc_version`, `ok`, and either `result` or an
error class. The server rejects malformed JSON, missing request identifiers, non-object arguments,
unknown operations and invalid operation arguments without exiting.

The submission operation carries traffic-unit identity, byte count, class and deferred intent. It
does not carry payload content.

## Reference security boundary

The server is hard-limited to `127.0.0.1`. That prevents external network reachability; it does not
authenticate a local process. There is no message authentication, authorisation, confidentiality,
replay defence, peer identity or resource quota beyond the one-megabyte request ceiling.

An operational binding needs authenticated peer identity and policy before it can control a
terminal or accept committed traffic. TLS on its own would not decide which process is authorised
to acquire a bearer, inject a fault or spend capacity.

## What S018 establishes

- adapter calls cross a separate server process;
- the same GX-A1 and GX-B1 versions remain visible at the boundary;
- malformed input receives a bounded error and the server remains alive;
- a restarted server resets link state while reopening the S017 traffic ledger; and
- the service process never imports a provider-specific terminal API.

Both server processes still run the GatewayCX reference implementation. Independent supplier
interoperability, authentication and hardware control remain open.
