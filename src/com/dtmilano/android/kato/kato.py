import sys
from collections import OrderedDict

from culebratester_client import Selector
from culebratester_client.rest import ApiException

from com.dtmilano.android.distance import levenshtein_distance

#
# https://en.wikipedia.org/wiki/Kato_(The_Green_Hornet)
#

DEBUG = False

ANYTHING = 'Pattern:^.*$'


class Kato:
    def __init__(self):
        self.enabled = False
        self.selectors = []
        self.distances = OrderedDict()


def kato(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            find_me_the_selectors(e, *args, **kwargs, func=func.__name__, distance_func=levenshtein_distance,
                                  distance_func_argument_mapper=str)

    return wrapper


def find_me_the_selectors(e: ApiException, *args, **kwargs):
    """
    Finds the selectors that would lead to a successful `find_object()`.
    The selectors found are added to the `selectors` list.

    :param e: the exception from a `find_object()` that couldn't find an object matching the selector
    :param args: args[0] is the UiDevice object
    :param kwargs:  - `body` the body of the request
                    - `distance_func` the distance function to apply
                    - `distance_func_argument_mapper` maps the arguments to distance_func from Selector to a type suitable
                    for that function
    :return: re-raise the original exception
    """
    if DEBUG:
        print('find_me_the_selectors', args, kwargs, file=sys.stderr)
    helper = args[0].uiAutomatorHelper
    msg = ''
    _d = dict()
    if helper.kato.enabled:
        if e.status == 404:
            distance = kwargs['distance_func']
            mapper = kwargs['distance_func_argument_mapper']
            helper.kato.selectors = list(map(lambda oid: helper.ui_object2.dump(oid),
                                             map(lambda obj_ref: obj_ref.oid,
                                                 helper.ui_device.find_objects(body={'text': ANYTHING}))))
            for n, s in enumerate(filter(lambda _s: helper.ui_device.has_object(body=_s), helper.kato.selectors)):
                if n == 0:
                    msg += 'Kato: selector distances:\n'
                d = distance(mapper(Selector(**kwargs['body'])), mapper(s))
                _d[d] = s
                msg += f'{d} -> {s}\n'
            helper.kato.distances = OrderedDict(sorted(_d.items(), reverse=False))
    raise ApiException(msg, e)
