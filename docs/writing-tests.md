
# Writing tests

We separate test between automatic and manual tests. Place the automatic tests in the following directory: test_folder/automated.

A basic test can look like the following:

```python
def step_1(dut: Dut):
    """
    action:
        Change ECU mode to programming mode/session
    expected_result:
        ECU is set to programming mode(mode=2)
    """

    dut.uds.set_mode(2)
    if dut.mode != 2:
      raise DutTestError("Setting ECU to programming mode failed")

def run():
    dut = Dut()
    start_time = dut.start()

    result = False
    try:
        dut.precondition()
        dut.step(step_1)
        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
```

## Device Under Test (DUT)

In an attempt to simplify test writing the Dut API was created. At the time of
writing there are still many test written using the old way of writing tests,
but do use the Dut API when writing new tests since that makes your work easier
and avoids code duplication.

## Basic configuration

You will find the basic configuration in
`projects/<platform>/parameters_yml/project_default.yml` where you can configure
the request and result frame to use for the ECU under test.

## Supporting multiple platforms with the same test

Althought the ODTB2 platform was created to initially test our BECM and the
newer HVBM ECU, it is by no means limited to those. Many of the test that we
create can be reused when testing various platform, however we might need to
provide the test with different parameters. That can be accomplished in test
itself by calling `get_platform()` or you can use yaml configuration files for
each platform that you place in the `projects/<platform>/parameters_yml`
directory.


## How to handle responses from the ECU

The reply from the ECU is basically just a hexstring and it can take some time
to decipher what the different bytes represent. Therefore, the framework
provides a mechnism for decomposing the reply from the ECU according to the UDS
standard (ISO-14229-1). One basic did is EDA0 that gives us the complete set of
ECU part/serial numbers. 

```python
response = dut.uds.read_data_by_id_22(EicDid.complete_ecu_part_number_eda0)
```

The raw response can look like this:

```
104A62EDA0F12032299361204142F12A32290749202020F12BFFFFFFFFFFFFFFF12E05322994
2520414532299427204143322994292041453229943020414132263666204141F18C30400011
```

That is not the most comprehensible chunk of data, so instead of interpreting
this in the test itself the framework can help us here. When we use the dut to
make a call to the ECU we actually get an UdsResponse object back.

```
UdsResponse:
  raw = 104A62EDA0...
  data =
    details:
      name: Complete ECU Part/Serial Number(s)
      size: 64
      item: F12032299361204142...
      F12A: 32290749202020
      F12A_info: {'name': 'ECU Core Assembly Part Number', 'size': 7}
      F12B: FFFFFFFFFFFFFF
      F12B_info: {'name': 'ECU Delivery Assembly Part Number', 'size': 7}
      F18C: 30400011
      F18C_info: {'name': 'ECU Serial Number', 'size': 4}
      F120: 32299361204142
      F120_info: {'name': 'Application Diagnostic Database Part Number', 'size': 7}
      F120_valid: 32299361 AB
      F12E: 0532299425204145322994272041433229942920414532299430204141
      F12E_info: {'name': 'ECU Software Part Numbers', 'size': 29, 'records': 5}
      F12E_list: ['32299425204145', '32299427204143', '32299429204145', '32299430204141', '32263666204141']
      F12E_valid: ['32299425 AE', '32299427 AC', '32299429 AE', '32299430 AA', '32263666 AA']
    sid: 62
    body: EDA0F12032299361204142...
    service: ReadDataByIdentifier
    did: EDA0
```

You can still use the raw data, but here we get all the data intrepreted for us.
What you see here as `data` is a dictionary, so we have direct access to all the
already interpreted fields. We even get them converted to proper ascii values if
the part/serial number corresponds to the specification for how such a field
should be formatted.

Then it becomes very easy to check that we get the correct value(s).

```python
if response.details["F120_valid"] != "32299361 AB":
    raise DutTestError("F120 returns incorrect part number")
```

Request parsing is currently implemented for EDA0 and F12C, but can easily be
extended to support other dids. It is also implemented for the following DTC request types:
 - Report DTC by status mask  (1902)
 - Report DTC snapshots ids (1903)
 - Report DTC snapshot (1904)
 - Report DTC extended data records (1906)

