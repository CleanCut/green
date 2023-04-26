# Import stuff you need for the unit tests themselves to work
import unittest

# Import stuff that you want to test.  Don't import extra stuff if you don't
# have to.
from proj.foo import answer, School

# If you need the whole module, you can do this:
#     from proj import foo
#
# Here's another reasonable way to import the whole module:
#     import proj.foo as foo
#
# In either case, you would obviously need to access objects like this:
#     foo.answer()
#     foo.School()

# Then write your tests


class TestAnswer(unittest.TestCase):
    def test_type(self):
        "answer() returns an integer"
        self.assertEqual(type(answer()), int)

    def test_expected(self):
        "answer() returns 42"
        self.assertEqual(answer(), 42)


class TestSchool(unittest.TestCase):
    def test_food(self):
        school = School()
        self.assertEqual(school.food(), "awful")

    def test_age(self):
        school = School()
        self.assertEqual(school.age(), 300)


# If there are doctests you would like to run, add a `doctest_modules` list to
# the top level of any of your test modules.  Items in the list are modules to
# discover doctests within.  Each item in the list can be either the name of a
# module as a dotted string or the actual module that has been imported.  In
# this case, we haven't actually imported proj.foo itself, so we use the string
# form of "proj.foo", but if we had done `import proj.foo` then we could have
# put the variable form proj.foo.  The module form is preferred as it results
# in both better performance and eliminates the chance that the discovery will
# encounter an error searching for the module.
doctest_modules = ["proj.foo"]
