from mjs_client.api.rpc import Lobby, Route, FastTest
from mjs_client.api.base import MSRPCChannel
import mjs_client.api.protocol_pb2 as pb
pb.Wrapper()

import mjs_client.client as client

from mjs_client.game.action_prototype_decode import decode

import time
import random
data = random.randbytes(10000000)

t1 = time.time()


decode(data)


t2 = time.time()
print(t2-t1)