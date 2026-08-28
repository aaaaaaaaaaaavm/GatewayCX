# S016 — GX-A1 executable bearer adapter probe

## Question

Can the same runtime control surface accept deferred traffic, apply profile-specific acquisition
and capacity, preserve a queue through a fault, and recover for the illustrative optical and RF
GX-B1 profiles?

## Method

`gatewaycx.adapter_probe` instantiates the same `ProfileBackedAdapter` once from each reference
profile. Each instance receives 122 traffic units of 65,536 bytes while unavailable, for a total
of 7,995,392 bytes. The probe then:

1. rejects an oversized unit and recognises a duplicate identifier;
2. establishes contact and waits exactly the profile's acquisition ceiling;
3. transmits for 100 ms using the profile's forward capacity;
4. injects `GX.BEARER.CONTACT_LOST` and attempts a blocked transmission;
5. confirms that queued bytes remain unchanged;
6. clears the fault, re-establishes contact, reacquires and drains the queue; and
7. compares the response-field signatures for every operation across both instances.

No payload bytes are supplied to the adapter. The probe operates on identifiers and byte counts.

## Result

| Profile instance | Assumed acquisition | First 100 ms | Queue at fault | Final ledger |
|---|---:|---:|---:|---:|
| Optical, 500 Mbps | 60 s | 6,250,000 B | 1,745,392 B | 7,995,392 B transmitted; 0 B queued |
| RF, 100 Mbps | 20 s | 1,250,000 B | 6,745,392 B | 7,995,392 B transmitted; 0 B queued |

Both instances expose the same response-field signature for all nine operations. Every local
acceptance, MTU, duplicate, capacity, fault, recovery and conservation check passes.

The deterministic record is [`results/S016_adapter_probe.json`](../results/S016_adapter_probe.json).

## What this closes

- The pre-draft GX-B1 documents can drive executable runtime capacity and acquisition behaviour.
- One service-plane method surface can exercise both reference media profiles.
- The reference adapter preserves committed byte-ledger state across its injected link fault.
- A reusable returned timestamp no longer fails because of floating-point representation noise.

## What remains open

Both instances use the same Python class. S016 is not the two-independent-adapter test required by
GX-INT-001, and no supplier software or hardware is represented. Capacity is a byte budget rather
than packets or a waveform. Acquisition is a deterministic timer, not pointing or modem lock.
Fault injection is in-process. There is no durable store across process failure, BPv7 engine,
authenticated control channel or out-of-process adapter binding.
