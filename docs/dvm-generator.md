
# DVM generator

Well written python can be read almost like english prose and comprehensible
even for non programmers. Therefore, we should aspire to make the test itself
it's own documentation; it's own DVM. Keeping the documentation close to where
it's being used adds clarity and easy of use. In that vain the following module
docstring was devised:

```python
"""
reqprod: 418372
version: 2
title: ECU Software Structure Part Number data record
purpose: To enable readout of the part number of the ECU Software Structure.
description: >
    If the ECU supports the Software Authentication concept where each data
    file is signed and verified individually as defined in ...
details:
    A ECU software part number should look like this: 32263666 AA.
precondition: ...
postcondition: ...
"""
```

By using valid yaml in the docstring we can easily parse it and use it, while
at the same time it reads really well so that you don't really notice that we
are actually dealing with structured data. This way it's a lot quicker to read
multiple tests where we previously had to bring up the test, look at the
reqprod number, then go to the SWRS document, search for the reqprod number,
and then do the same thing for the next test, and the following, and so on. So
it's better for auditors, testers, and other parties involved.

Each step can be documented in the same way in the function docstring as
follows:

```python
def step_1(dut):
    """
    action:
        Get the complete ECU part numbers from another did to have something to
        compare it with
 
    expected_result: >
        ECU: Positive response
 
    comment:
        All the part numbers should be returned
    """
```

The DVM generator then steps through the functions in the file and collects
that data for the table in the DVM file that describes each step. Currently the
DVM report is in docx format, but we might want to consider actually using html
moving forward since that makes further extensions easier to handle.

To generate the DVM document, all you need to do is to run the following:

```
./manage.py dvm <name_of_test>
```

Then you will get a nicely formatted `REQ_12345_name_of_test.docx` in the current directory.
