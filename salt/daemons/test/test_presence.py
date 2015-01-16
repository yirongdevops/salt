# -*- coding: utf-8 -*-
"""
Raet Ioflo Behavior Unittests
"""

import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from ioflo.base.consoling import getConsole
console = getConsole()
from ioflo.base.odicting import odict
from ioflo.test import testing

from raet.lane.stacking import LaneStack
from raet.stacking import Stack

from salt.utils.event import tagify

# Import Ioflo Deeds
from salt.daemons.flo import core
from salt.daemons.test.plan import actors


def setUpModule():
    console.reinit(verbosity=console.Wordage.concise)

def tearDownModule():
    pass


class PresenterTestCase(testing.FrameIofloTestCase):
    """
    Test case for Salt Raet Presenter deed
    """

    def setUp(self):
        """
        Call super if override so House Framer and Frame are setup correctly
        """
        super(PresenterTestCase, self).setUp()
        self.addBenterDeed("SaltRaetTestOptsSetup")
        self.addBenterDeed("SaltRaetManorLaneSetup")
        self.addBenterDeed("SaltRaetPresenterTestSetup")

        self.act = self.addEnterDeed("SaltRaetPresenter")
        self.assertIn(self.act, self.frame.enacts)
        self.assertEqual(self.act.actor, "SaltRaetPresenter")

        self.resolve()  # resolve House, Framer, Frame, Acts, Actors
        self.frame.checkEnter()
        self.assertDictEqual(self.act.actor.Ioinits,
                             {'opts': '.salt.opts',
                              'presence_req': '.salt.presence.event_req',
                              'lane_stack': '.salt.lane.manor.stack',
                              'alloweds': '.salt.var.presence.alloweds',
                              'aliveds': '.salt.var.presence.aliveds',
                              'reapeds': '.salt.var.presence.reapeds',
                              'availables': '.salt.var.presence.availables'})

        self.assertTrue(hasattr(self.act.actor, 'opts'))
        self.assertTrue(hasattr(self.act.actor, 'presence_req'))
        self.assertTrue(hasattr(self.act.actor, 'lane_stack'))
        self.assertTrue(hasattr(self.act.actor, 'alloweds'))
        self.assertTrue(hasattr(self.act.actor, 'aliveds'))
        self.assertTrue(hasattr(self.act.actor, 'reapeds'))
        self.assertTrue(hasattr(self.act.actor, 'availables'))
        self.assertIsInstance(self.act.actor.lane_stack.value, LaneStack)


    def tearDown(self):
        """
        Call super if override so House Framer and Frame are torn down correctly
        """
        self.act.actor.lane_stack.value.server.close()
        testStack = self.store.fetch('.salt.test.lane.stack').value
        testStack.server.close()

        super(PresenterTestCase, self).tearDown()


    def addPresenceInfo(self, stateGrp, name, ip, port):
        self.assertIn(stateGrp, ('alloweds', 'aliveds', 'reapeds'))
        group = self.store.fetch('.salt.var.presence.{0}'.format(stateGrp))
        if group.value is None:
            group.value = odict()
        remote = Stack()
        remote.ha = (ip, port)
        group.value[name] = remote


    def addAvailable(self, name):
        availables = self.store.fetch('.salt.var.presence.availables')
        if availables.value is None:
            availables.value = set()
        availables.value.add(name)


    def testPresenceAvailable(self):
        """
        Test Presenter 'available' request (A1, B*)
        """
        console.terse("{0}\n".format(self.testPresenceAvailable.__doc__))

        # Prepare
        # add available minions
        self.addAvailable('alpha')
        self.addAvailable('beta')
        self.addPresenceInfo('aliveds', 'alpha', '1.1.1.1', '1234')
        self.addPresenceInfo('aliveds', 'beta', '1.2.3.4', '1234')
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        # general available request format
        presenceReq.append({'route': {'dst': (None, ryn, 'presence_req'),
                                      'src': (None, testStack.local.name, None)},
                            'data': {'state': 'available'}})
        # missing 'data', fallback to available
        presenceReq.append({'route': {'dst': (None, ryn, 'presence_req'),
                                      'src': (None, testStack.local.name, None)}})
        # missing 'state' in 'data', fallback to available
        presenceReq.append({'route': {'dst': (None, ryn, 'presence_req'),
                                      'src': (None, testStack.local.name, None)},
                            'data': {}})
        # requested None state, fallback to available
        presenceReq.append({'route': {'dst': (None, ryn, 'presence_req'),
                                      'src': (None, testStack.local.name, None)},
                            'data': {'state': None}})
        # requested 'present' state that is alias for available
        presenceReq.append({'route': {'dst': (None, ryn, 'presence_req'),
                                      'src': (None, testStack.local.name, None)},
                            'data': {'state': 'present'}})

        # Test
        # process 5 requests at once
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 5)

        tag = tagify('present', 'presence')
        while testStack.rxMsgs:
            msg, sender = testStack.rxMsgs.popleft()
            self.assertDictEqual(msg, {'route': {'src': [None, 'manor', None],
                                                 'dst': [None, None, 'event_fire']},
                                       'tag': tag,
                                       'data': {'present': {'alpha': '1.1.1.1',
                                                            'beta': '1.2.3.4'}}})


    def testPresenceJoined(self):
        """
        Test Presenter 'joined' request (A2)
        """
        console.terse("{0}\n".format(self.testPresenceJoined.__doc__))

        # Prepare
        # add joined minions
        # NOTE: for now alloweds are threaded as joineds
        self.addPresenceInfo('alloweds', 'alpha', '1.1.1.1', '1234')
        self.addPresenceInfo('alloweds', 'beta', '1.2.3.4', '1234')
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        msg = {'route': {'dst': (None, ryn, 'presence_req'),
                         'src': (None, testStack.local.name, None)},
               'data': {'state': 'joined'}}
        presenceReq.append(msg)

        # Test
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 1)

        tag = tagify('present', 'presence')
        msg, sender = testStack.rxMsgs.popleft()
        self.assertDictEqual(msg, {'route': {'src': [None, 'manor', None],
                                             'dst': [None, None, 'event_fire']},
                                   'tag': tag,
                                   'data': {'joined': {'alpha': '1.1.1.1',
                                                       'beta': '1.2.3.4'}}})


    def testPresenceAllowed(self):
        """
        Test Presenter 'allowed' request (A3)
        """
        console.terse("{0}\n".format(self.testPresenceAllowed.__doc__))

        # Prepare
        # add allowed minions
        self.addPresenceInfo('alloweds', 'alpha', '1.1.1.1', '1234')
        self.addPresenceInfo('alloweds', 'beta', '1.2.3.4', '1234')
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        msg = {'route': {'dst': (None, ryn, 'presence_req'),
                         'src': (None, testStack.local.name, None)},
               'data': {'state': 'allowed'}}
        presenceReq.append(msg)

        # Test
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 1)

        tag = tagify('present', 'presence')
        msg, sender = testStack.rxMsgs.popleft()
        self.assertDictEqual(msg, {'route': {'src': [None, 'manor', None],
                                             'dst': [None, None, 'event_fire']},
                                   'tag': tag,
                                   'data': {'allowed': {'alpha': '1.1.1.1',
                                                        'beta': '1.2.3.4'}}})


    def testPresenceAlived(self):
        """
        Test Presenter 'alived' request (A4)
        """
        console.terse("{0}\n".format(self.testPresenceAlived.__doc__))

        # Prepare
        # add alived minions
        self.addPresenceInfo('aliveds', 'alpha', '1.1.1.1', '1234')
        self.addPresenceInfo('aliveds', 'beta', '1.2.3.4', '1234')
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        msg = {'route': {'dst': (None, ryn, 'presence_req'),
                         'src': (None, testStack.local.name, None)},
               'data': {'state': 'alived'}}
        presenceReq.append(msg)

        # Test
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 1)

        tag = tagify('present', 'presence')
        msg, sender = testStack.rxMsgs.popleft()
        self.assertDictEqual(msg, {'route': {'src': [None, 'manor', None],
                                             'dst': [None, None, 'event_fire']},
                                   'tag': tag,
                                   'data': {'alived': {'alpha': '1.1.1.1',
                                                       'beta': '1.2.3.4'}}})


    def testPresenceReaped(self):
        """
        Test Presenter 'reaped' request (A5)
        """
        console.terse("{0}\n".format(self.testPresenceReaped.__doc__))

        # Prepare
        # add reaped minions
        self.addPresenceInfo('reapeds', 'alpha', '1.1.1.1', '1234')
        self.addPresenceInfo('reapeds', 'beta', '1.2.3.4', '1234')
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        msg = {'route': {'dst': (None, ryn, 'presence_req'),
                         'src': (None, testStack.local.name, None)},
               'data': {'state': 'reaped'}}
        presenceReq.append(msg)

        # Test
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 1)

        tag = tagify('present', 'presence')
        msg, sender = testStack.rxMsgs.popleft()
        self.assertDictEqual(msg, {'route': {'src': [None, 'manor', None],
                                             'dst': [None, None, 'event_fire']},
                                   'tag': tag,
                                   'data': {'reaped': {'alpha': '1.1.1.1',
                                                       'beta': '1.2.3.4'}}})


    def testPresenceNoRequest(self):
        """
        Test Presenter with no requests (C1)
        """
        console.terse("{0}\n".format(self.testPresenceNoRequest.__doc__))

        # Test
        self.frame.enter()  # run in frame

        # Check
        testStack = self.store.fetch('.salt.test.lane.stack').value
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 0)


    def testPresenceUnknownSrc(self):
        """
        Test Presenter handles request from unknown (disconnected) source (C2)
        """
        console.terse("{0}\n".format(self.testPresenceUnknownSrc.__doc__))

        # Prepare
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        name = 'unknown_name'
        self.assertNotEqual(name, testStack.local.name)
        msg = {'route': {'dst': (None, ryn, 'presence_req'),
                         'src': (None, name, None)}}
        presenceReq.append(msg)

        # Test
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 0)


    def testPresenceAvailableNoMinions(self):
        """
        Test Presenter 'available' request with no minions in the state (D1)
        """
        console.terse("{0}\n".format(self.testPresenceAvailableNoMinions.__doc__))

        # Prepare
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        presenceReq.append({'route': {'dst': (None, ryn, 'presence_req'),
                                      'src': (None, testStack.local.name, None)},
                            'data': {'state': 'available'}})

        # Test
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 1)

        tag = tagify('present', 'presence')
        msg, sender = testStack.rxMsgs.popleft()
        self.assertDictEqual(msg, {'route': {'src': [None, 'manor', None],
                                             'dst': [None, None, 'event_fire']},
                                   'tag': tag,
                                   'data': {'present': {}}})


    def testPresenceAvailableOneMinion(self):
        """
        Test Presenter 'available' request with one minion in the state (D2)
        """
        console.terse("{0}\n".format(self.testPresenceAvailableOneMinion.__doc__))

        # Prepare
        # add available minions
        self.addAvailable('alpha')
        self.addPresenceInfo('aliveds', 'alpha', '1.1.1.1', '1234')
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        presenceReq.append({'route': {'dst': (None, ryn, 'presence_req'),
                                      'src': (None, testStack.local.name, None)},
                            'data': {'state': 'available'}})

        # Test
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 1)

        tag = tagify('present', 'presence')
        msg, sender = testStack.rxMsgs.popleft()
        self.assertDictEqual(msg, {'route': {'src': [None, 'manor', None],
                                             'dst': [None, None, 'event_fire']},
                                   'tag': tag,
                                   'data': {'present': {'alpha': '1.1.1.1'}}})


    def testPresenceAvailableSomeIpUnknown(self):
        """
        Test Presenter 'available' request with some minion addresses aren't known (D3)
        """
        console.terse("{0}\n".format(self.testPresenceAvailableSomeIpUnknown.__doc__))

        # Prepare
        # add available minions
        self.addAvailable('alpha')
        self.addAvailable('beta')
        self.addAvailable('gamma')
        self.addPresenceInfo('aliveds', 'alpha', '1.1.1.1', '1234')
        self.addPresenceInfo('aliveds', 'delta', '1.2.3.4', '1234')
        # add presence request
        testStack = self.store.fetch('.salt.test.lane.stack').value
        presenceReq = self.store.fetch('.salt.presence.event_req').value
        ryn = 'manor'
        presenceReq.append({'route': {'dst': (None, ryn, 'presence_req'),
                                      'src': (None, testStack.local.name, None)},
                            'data': {'state': 'available'}})

        # Test
        self.frame.enter()  # run in frame

        # Check
        self.assertEqual(len(testStack.rxMsgs), 0)
        testStack.serviceAll()
        self.assertEqual(len(testStack.rxMsgs), 1)

        tag = tagify('present', 'presence')
        msg, sender = testStack.rxMsgs.popleft()
        self.assertDictEqual(msg, {'route': {'src': [None, 'manor', None],
                                             'dst': [None, None, 'event_fire']},
                                   'tag': tag,
                                   'data': {'present': {'alpha': '1.1.1.1',
                                                        'beta': None,
                                                        'gamma': None}}})


def runOne(test):
    '''
    Unittest Runner
    '''
    test = PresenterTestCase(test)
    suite = unittest.TestSuite([test])
    unittest.TextTestRunner(verbosity=2).run(suite)


def runSome():
    """ Unittest runner """
    tests = []
    names = [
        'testPresenceAvailable',
        'testPresenceJoined',
        'testPresenceAllowed',
        'testPresenceAlived',
        'testPresenceReaped',
        'testPresenceNoRequest',
        'testPresenceUnknownSrc',
        'testPresenceAvailableNoMinions',
        'testPresenceAvailableOneMinion',
        'testPresenceAvailableSomeIpUnknown',
        ]
    tests.extend(map(PresenterTestCase, names))
    suite = unittest.TestSuite(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)


def runAll():
    """ Unittest runner """
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PresenterTestCase))
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__' and __package__ is None:

    # console.reinit(verbosity=console.Wordage.concise)

    runAll()  # run all unittests

    # runSome()  #only run some

    # runOne('testPresenceAvailable')
