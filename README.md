# Reliable Transport Protocol

## Design of My Protocol
I chose to store my messages in the JSON format, which provided ease in encoding and decoding the messages. Even though this added some overhead, I found JSON to be a more user-friendly format. Initially, I considered encoding the packets in binary using the `struct` package, but it seemed a bit cumbersome.

In my protocol, every message sent contains an `id`. This integer allows me to track the packets I've sent and received.

Messages also feature a `type` value, indicating their purpose. In this project, the possible values for `type` are `msg` and `ack`. A `type: msg` indicates data delivery, while a `type: ack` acknowledges a packet from the other party.

Messages with the `msg` type also include a `data` field for transmitting data.

Lastly, I introduced a `checksum` field to determine if a message is corrupted. Leveraging the `json` library for encoding and decoding facilitates error detection through the `loads` function. If this function encounters a decoding error, the message is likely corrupt and is discarded. This two-tiered corruption check ensures the integrity of the data I send and receive.

## High-level Approach
Much of the high-level approach regarding my protocol is outlined above. I chose `Python` for this project due to my familiarity with it and the availability of starter code in the same language. Using the starter code as a foundation, I began integrating features specified in the project documentation. To sequentially develop the functions, I relied on the "Implementation Strategy" section of the project description.

## Challenges
One initial challenge was determining the ideal message format. I initially considered moving away from JSON in favor of the `struct` package, which converts Python data into byte strings. The allure was binary encoding to reduce JSON's overhead.

However, using the `struct` package proved problematic. I encountered multiple message encoding errors, leading me to revert to JSON. Though I hoped to implement the `struct` package successfully, I prioritized a smoother project progression.

Another challenge was understanding the interaction between the `Sender` and `Receiver` during advanced tests. Print debugging proved invaluable, providing insights into each party's state and troubleshooting issues like incorrect `time_out` values or error detection.

## Good Features
I organized the functionality of the Sender and Receiver into distinct helper functions, which were called based on context. In the `Sender` class, I isolated functionalities related to time-outs and RTT calculations into separate helper methods. This modular approach simplified the primary loop, as most project functionalities were encapsulated within these helpers.

I'm also proud of the two-step message verification I implemented. I check the `checksum` of data messages to detect minor errors in the `data` segment. Additionally, I use the `loads` function of the `json` library to identify messages that cannot be parsed correctly. This dual approach effectively identifies message errors, leading to the appropriate discarding of corrupt packets.

## How I Tested
For testing, I combined print debugging with the provided config files. I approached one test level at a time, advancing only after ensuring satisfactory performance. However, as I delved deeper into the project, complexities increased, especially when functionalities from advanced levels affected earlier tests. Fortunately, the requirements of the final stages ensured I passed all provided tests.