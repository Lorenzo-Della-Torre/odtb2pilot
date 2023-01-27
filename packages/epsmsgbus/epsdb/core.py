"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

#!/bin/env python
"""
Read JSON messages in Cynosure 2.0 format and insert data in database.
"""

import dateutil.parser
import logging
import re

import epsconfig

from collections import OrderedDict


log = logging.getLogger("epsdb.core")


# Globals ================================================================{{{1
DEFAULT_CONFIG_NAME = 'db'

TEST_FRAMEWORK = 'Hilding'
TEST_ENVIRONMENT = 'pirig'


# Database configuration ================================================={{{1
class DatabaseConfiguration(object):
    """Database configuration - try to disable if not configured correctly."""
    enabled = False
    dbtype = 'NULL'
    connstr = []

    def __init__(self, name=DEFAULT_CONFIG_NAME):
        c = epsconfig.config(name)
        if c:
            self.enabled = c.database.enabled or False
            self.dbtype = c.database.type
            self.connstr = []
            for opt in c.database:
                if opt.name.startswith('connstr'):
                    self.connstr.append(opt.value)
        else:
            log.warning("No configuration files found, database operations will be disabled.")


try:
    CONFIG
except NameError:
    CONFIG = DatabaseConfiguration()


# Message format version ================================================={{{1
# Unfortunately we need to parse the messages slightly different between
# versions 2 and 3
CYNOSURE_MAJOR_VERSION = epsconfig.config(DEFAULT_CONFIG_NAME).cynosure.major_version or 0


# Basic database functions ==============================================={{{1
class NullDatabase(object):
    """if pyodbc is not installed/configured, then fake all database
    operations."""
    def connect(self, *a, **k):
        return self

    def cursor(self, *a, **k):
        return self

    def execute(self, *a, **k):
        log.debug("Database disabled (NullDatabase).")

    def commit(self, *a, **k):
        pass

    def rollback(self, *a, **k):
        pass

    def close(self, *a, **k):
        pass


class ConnectionFactory(object):
    def __init__(self, enabled, dbtype, *connstr):
        """Dispatch to the configured database type. If 'pyodbc' is not
        configured, then fake the database.
        IMPORTANT: Run init() the first time an SQLite database is used to
        create all necessary database objects!"""
        log.debug(self.hide_password("ConnectionFactory(%s, '%s', %s)" % (enabled, dbtype, connstr)))
        self.connstr = connstr
        if not enabled:
            self.dbmod = NullDatabase()
        elif dbtype.upper() == 'MSSQL':
            try:
                import pyodbc
                self.dbmod = pyodbc
            except Exception as e:
                log.error("Could not instantiate pyodbc driver [%s].", e)
                log.debug("TRACE", exc_info=True)
                self.dbmod = NullDatabase()
        elif dbtype.upper() == 'SQLITE':
            import sqlite3
            self.dbmod = sqlite3
        else:
            log.error("The database type '%s' is not supported. Database operations will be disabled.", dbtype)
            self.dbmod = NullDatabase()

    def hide_password(self, string):
        """Avoid printing out passwords to log files."""
        return re.sub('(?i)(p(ass)?w(or)?d)=[^;]*', r'\1=*****', string)

    def connection(self):
        """Return database connection object (DBI)."""
        try:
            return self.dbmod.connect(*self.connstr)
        except Exception as e:
            log.error(e)
            log.debug("TRACE", exc_info=True)
            log.warning("Cannot connect to database, database operations will be disabled.")
            self.dbmod = NullDatabase()
            return NullDatabase()


class DatabaseContext(object):
    """Context where a database connection is set up."""
    def __init__(self, factory=None):
        """Connect to database and create cursor."""
        if factory is None:
            factory = connection_factory()
        self.connection = factory.connection()
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        """Commit unless there was an error in which case we roll back. Close
        connection and cursor."""
        if t is None and v is None and tb is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.close()

    def close(self):
        """Close cursor and connection."""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()

    def sql(self, statement, args=None):
        """Run SQL statement with arguments."""
        if args is None:
            log.debug("SQL: %s" % statement)
            return self.cursor.execute(statement)
        else:
            log.debug("SQL: %s <-> %s" % (statement, args))
            return self.cursor.execute(statement, args)



# Data mappings from JSON to database columns ============================{{{1
class CommonMapping(object):
    """These fields are the same for test suite/test case/test step."""

    def description(self, msg):
        """Column 'description'."""
        return self.safe_get(msg, 'custom', 'EPSHIL_description').strip()

    def start_time(self, msg):
        """Column 'start_time'."""
        return self._to_time(self.safe_get(msg, 'custom', 'EPSHIL_ini_execution_time'))

    def end_time(self, msg):
        """Column 'end_time'."""
        return self._to_time(self.safe_get(msg, 'custom', 'EPSHIL_end_execution_time'))

    def testsuite_result(self, msg):
        """Column 'testsuite_result'."""
        if CYNOSURE_MAJOR_VERSION > 2:
            return self.safe_get(msg, 'activityId')
        else:
            return self.safe_get(msg, 'activityId', 'instance')

    def verdict(self, msg):
        """Column 'verdict'."""
        return self.safe_get(msg, 'verdict')

    def _to_time(self, data):
        """Help function to fix dates/times for MS SQL."""
        if CONFIG.dbtype == 'MSSQL':
            # convert 127 is for ISO-8601 with milliseconds and timezone Z
            # return "convert(datetime, '%s', 127)" % data.replace('000Z', 'Z')
            return dateutil.parser.isoparse(data)
        return data

    def safe_get(self, mapping, *keys):
        value = mapping
        for key in keys:
            value = value.get(key, {})
        return value or ''

    def find_version_info(self, key, version_info_list):
        """Return version_info_listonary with the information requested for a specific name (key)"""
        is_found = False
        item = None
        element = 0
        while not is_found and element < len(version_info_list):
            aux = version_info_list[element]
            if key == aux.get('name'):
                is_found = True
                item = aux
            else:
                element+=1
        return item



class TestsuiteResultMapping(CommonMapping):
    """Mappings for table 'testsuite_result'."""
    def __init__(self):
        self.ecus = []
        self.platforms = []
        self.projects = []
        with DatabaseContext() as db:
            self.ecus = [x for x, in db.sql('SELECT name FROM ecu').fetchall()]
            self.platforms = [x for x, in db.sql('SELECT name FROM platform').fetchall()]
            self.projects = [x for x, in db.sql('SELECT name FROM vehicle_project').fetchall()]

    def uuid(self, msg):
        """Column 'uuid' - the test suite id."""
        if CYNOSURE_MAJOR_VERSION > 2:
            return self.safe_get(msg, 'activityId')
        else:
            return self.safe_get(msg, 'activityId', 'instance')

    def name(self, msg):
        """Column 'name'."""
        if CYNOSURE_MAJOR_VERSION > 2:
            return self.safe_get(msg, 'name').split('/')[-1]
        else:
            return self.safe_get(msg, 'activityId', 'namespace')

    def ad_project(self, msg):
        """AutomationDesk project used in the tests."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_project_AD_name')

    def changeset(self, msg):
        """Column 'baseline_changeset'."""
        value = self.safe_get(msg, 'custom', 'EPSHIL_Baseline_Changeset')
        try: 
            value = int(value)
        except:
            pass
        return value

    def description(self, msg):
        """Override for column 'description'."""
        
        return self.safe_get(msg, 'custom', 'EPSHIL_TestExecutionDescription')

    def devchgnum(self, msg):
        """Column 'baseline_changeset'."""
        # Return None if empty to avoid FK constraint problems
        value = self.safe_get(msg, 'custom', 'EPSHIL_Development_Baseline_Changeset')
        try: 
            value = int(value)
        except:
            pass
        return value

    def ecu(self, msg):
        """ECU - will only return value if ECU exists in catalog data."""
        # Return ecu if ecu in catalog data else None
        ecu = self.ecu_raw(msg)
        if ecu in self.ecus:
            return ecu

    def ecu_raw(self, msg):
        """ECU as entered in test environment."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_ECU')

    def executor(self, msg):
        """CDSID of person that started execution."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_executor')

    def git_hash(self, msg):
        """Git Hash (from JSON file used for CI)."""
        return self.safe_get(msg, 'custom', 'EPSHIL_GitHash')

    def jenkins_jobid(self, msg):
        """The (Jenkins) job id for the test job itself."""
        return self.safe_get(msg, 'custom', 'EPSHIL_Jenkins_JobId')

    def model_can_db(self, msg):
        """CAN database used in the simulation model."""
        return self.safe_get(msg, 'custom', 'EPSHIL_Model_CAN_database')

    def model_ecu(self, msg):
        """ECU id for the simulation application."""
        return self.safe_get(msg, 'custom', 'EPSHIL_Model_ECU')

    def model_id(self, msg):
        """Simulation application identity.."""
        return self.safe_get(msg, 'custom', 'EPSHIL_Model_id')

    def model_project(self, msg):
        """Simulation application project.."""
        return self.safe_get(msg, 'custom', 'EPSHIL_Model_project')

    def partnums(self, msg):
        """Software part numbers."""
        return self.safe_get(msg, 'custom', 'EPSHIL_SWPartNumbers') or []

    def hwpartnums(self, msg):
        """Software part numbers."""
        return self.safe_get(msg, 'custom', 'EPSHIL_HWPartNumbers') or []

    def relver(self, msg):
        """Software release version identifier."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_release_version')

    def system_name(self, msg):
        """System name (identity of the simulator and/or equipment)."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_name')

    def vehicle_platform(self, msg):
        """Vehicle platform - only return value if it exists in catalog data."""
        # Return platform if platform in catalog data else None
        platform = self.vehicle_platform_raw(msg)
        if platform in self.platforms:
            return platform

    def vehicle_platform_raw(self, msg):
        """Return vehicle platform as entered in AutomationDesk project."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_platform')

    def vehicle_project(self, msg):
        """Vehicle project - only return value if it exists in catalog data."""
        # Return project if project in catalog data else None
        project = self.vehicle_project_raw(msg)
        if project in self.projects:
            return project

    def vehicle_project_raw(self, msg):
        """Return vehicle project as entered in AutomationDesk project."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_project')

    def vehicle_series(self, msg):
        """Vehicle series."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_series') or '-'

    def version_framework(self,msg):
        """Return framework repo version"""
        return self.find_version_info('framework', self.safe_get(msg, 'custom', 'EPSHIL_System_repo_information'))

    def version_test(self,msg):
        """Return test repo version"""
        return self.find_version_info('test', self.safe_get(msg, 'custom', 'EPSHIL_System_repo_information'))

    def sw_tag(self, msg):
        """Return sw tag."""
        return self.safe_get(msg, 'custom', 'EPSHIL_Software_tag')

    def automation_desk_version(self, msg):
        """Return AutomationDesk version."""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_AD_Version')

    def package_url(self,msg):
        """Return package url to artifactory .zip"""
        custom = self.safe_get(msg, 'custom', 'EPSHIL_package_url')
        if custom == '':
            custom = self.safe_get(msg, 'revision', 'previous', 'custom', 'EPSHIL_package_url')
        return custom
    
    def test_equipment(self,msg):
        """Return test equipment identifier"""
        return self.safe_get(msg, 'custom', 'EPSHIL_System_testequipment')


class TestcaseResultMapping(CommonMapping):
    """Mappings for table 'testcase_result'."""

    def uuid(self, msg):
        """Column 'uuid' - the test suite id."""
        if CYNOSURE_MAJOR_VERSION > 2:
            return self.safe_get(msg, 'taskId')
        else:
            return self.safe_get(msg, 'taskId', 'instance')

    def name(self, msg):
        """Column 'name'."""
        if CYNOSURE_MAJOR_VERSION > 2:
            return self.safe_get(msg, 'name').split('/')[-1]
        else:
            return self.safe_get(msg, 'taskId', 'namespace')

    def requirement_id(self, msg):
        """Not stored in testcase result, using work-around
        function temporarily."""
        return self.safe_get(msg, 'custom', 'EPSHIL_requirement')

    def responsible(self, msg):
        """Not stored in testcase result, using work-around
        function temporarily."""
        return self.safe_get(msg, 'custom', 'EPSHIL_TCresponsible')


class TeststepResultMapping(CommonMapping):
    """Mappings for table 'teststep_result'."""

    def name(self, msg):
        """Column 'name'."""
        if CYNOSURE_MAJOR_VERSION > 2:
            return self.safe_get(msg, 'name').split('/')[-1]
        else:
            return self.safe_get(msg, 'taskId', 'namespace')

    def testcase_result(self, msg):
        """Column 'testcase_result'."""
        if CYNOSURE_MAJOR_VERSION > 2:
            return self.safe_get(msg, 'parentTaskId')
        else:
            return self.safe_get(msg, 'parentTaskId', 'namespace')


# Insert new data in requirements tables ================================={{{1
class RequirementParser(object):
    re_req = re.compile(r'^(REQPROD)?[_ ]*(?P<number>\d{2,})(/(?P<branch>[A-Za-z][^/]*))?(/(?P<revision>\d+))?(?P<rest>.*)$')
    re_handle_id = re.compile(r'^([x,X])(?P<number>\d{16,})(/(?P<branch>[A-Za-z][^/]*))?(/(?P<revision>\d+))?(?P<rest>.*)$') #check 16 elements
    def __init__(self, reqstring):
        self.number = self.revision = -1
        self.branch = '-'
        self.req = reqstring
        m_req = self.re_handle_id.match(reqstring) if reqstring.startswith(('x','X')) else self.re_req.match(reqstring)
        if m_req:
            # The typecast to int should always work since both number and
            # revision only gives a match for numbers
            self.number = m_req.group('number')
            self.branch = '-' if m_req.group('branch') is None else m_req.group('branch').upper()
            if m_req.group('revision'):
                self.revision = m_req.group('revision')

    def __repr__(self):
        return self.key

    def __str__(self):
        return self.id

    @property
    def id(self):
        def mapping_req():
            return 'x' if self.req.startswith(('x','X')) else 'REQPROD '
        
        if self.number:
            if self.branch:
                if self.revision:
                    return mapping_req() + '{}/{}/{}'.format(self.number, self.branch, self.revision)
                else:
                    return mapping_req() + '{}/{}'.format(self.number, self.branch)
            else:
                if self.revision:
                    return mapping_req() + '{} Revision {}'.format(self.number, self.revision)
                else:
                    return mapping_req() + '{}'.format(self.number)
        else:
            return ''

    @property
    def key(self):
        default = '{}:{}:{}'.format(self.number, self.revision, self.branch) 
        return 'x%s' % self.number if self.req.startswith(('x','X')) else default


# Database insert/update statements ======================================{{{1
class DataMapper(object):
    """Open connection and perform DML command."""

    def __init__(self, mapping):
        self.mapping = mapping

    def store(self, msg):
        """Run SQL command in context to assure proper handling."""
        with DatabaseContext() as db:
            db.sql(self.command, self.values(msg))

    def add_attribute(self, db, uuid, attribute, value):
        """Add attribute to runtime_data - to connect part numbers that have been read."""
        if value:
            db.sql("INSERT INTO runtime_data (testsuite_result, attribute, value) VALUES (?, ?, ?)",
                    (uuid, attribute, value))
        else:
            log.debug("The attribute '%s' had no value, not added to 'runtime_data'." % attribute)


class TestsuiteResultInsert(DataMapper):
    """Create new record in 'testsuite_result'."""

    command = (
        "INSERT INTO testsuite_result"
        "   (pkey, name, description, executor, start_time, status, verdict,"
        "        testcase_tool, environment, ecu, vehicle_project, platform,"
        "        development_baseline, release_baseline)"
        "  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

    def values(self, msg):
        """Return mappings."""
        return (
            self.mapping.uuid(msg),
            self.mapping.name(msg),
            self.mapping.description(msg),
            self.mapping.executor(msg),
            self.mapping.start_time(msg),
            'ongoing',
            'unknown',
            TEST_FRAMEWORK,
            TEST_ENVIRONMENT,
            self.mapping.ecu(msg),
            self.mapping.vehicle_project(msg),
            self.mapping.vehicle_platform(msg),
            self.mapping.devchgnum(msg),
            self.mapping.changeset(msg))

    def store(self, msg):
        super(TestsuiteResultInsert, self).store(msg)
        uuid = self.mapping.uuid(msg)
        changeset = self.mapping.changeset(msg)
        devchgnum = self.mapping.devchgnum(msg)
        vehicle_series = self.mapping.vehicle_series(msg)
        relver = self.mapping.relver(msg)
        with DatabaseContext() as db:
            # Store in 'runtime_data'
            self.add_attribute(db, uuid, 'git_hash', self.mapping.git_hash(msg))
            self.add_attribute(db, uuid, 'jenkins_jobid', self.mapping.jenkins_jobid(msg))
            self.add_attribute(db, uuid, 'can_db', self.mapping.model_can_db(msg))
            self.add_attribute(db, uuid, 'model_ecu', self.mapping.model_ecu(msg))
            self.add_attribute(db, uuid, 'hil_model_id', self.mapping.model_id(msg))
            self.add_attribute(db, uuid, 'model_project', self.mapping.model_project(msg))
            self.add_attribute(db, uuid, 'system_name', self.mapping.system_name(msg))
            self.add_attribute(db, uuid, 'system_ecu', self.mapping.ecu_raw(msg))
            self.add_attribute(db, uuid, 'system_platform', self.mapping.vehicle_platform_raw(msg))
            self.add_attribute(db, uuid, 'system_AD_project', self.mapping.ad_project(msg))
            self.add_attribute(db, uuid, 'system_series', vehicle_series)
            self.add_attribute(db, uuid, 'system_vehicle_project', self.mapping.vehicle_project_raw(msg))
            self.add_attribute(db, uuid, 'system_release_version', relver)
            self.add_attribute(db, uuid, 'release_baseline', changeset)

            # If self.mapping.version_framework(msg) is 'NoneType' we get an exception when we execute 'get'.
            # That is why we have this extra check
            version_framework = self.mapping.version_framework(msg)
            if isinstance(version_framework, dict):
                self.add_attribute(db, uuid, 'epc_framework_repo',  version_framework.get('revision'))
            else:
                self.add_attribute(db, uuid, 'epc_framework_repo', '')

            # If self.mapping.version_framework(msg) is 'NonType' we get an exception when we execute 'get'.
            # That is why we have this extra check
            version_test = self.mapping.version_test(msg)
            if isinstance(version_test, dict):
                self.add_attribute(db, uuid, 'epc_test_repo', version_test.get('revision'))
            else:
                self.add_attribute(db, uuid, 'epc_test_repo', '')

            self.add_attribute(db, uuid, 'automation_desk_version', self.mapping.automation_desk_version(msg))
            package_urls = self.mapping.package_url(msg)
            if isinstance(package_urls, list):
                for i, package_url in enumerate(package_urls, start=1):
                    self.add_attribute(db, uuid, 'package_url_'+str(i), package_url)
            else:
                self.add_attribute(db, uuid, 'package_url_1', self.mapping.package_url(msg))
            for i, test_equipment in enumerate(self.mapping.test_equipment(msg), start=1):
                self.add_attribute(db, uuid, 'test_equipment_'+str(i), test_equipment)
        if devchgnum:
            with DatabaseContext() as db:
                # Create baseline if not exists, save in own transaction
                merge_stmt = (
                    "MERGE release_baseline AS target"
                    "  USING (values (?))"
                    "    AS source (change_id)"
                    "    ON target.change_id = source.change_id"
                    "  WHEN NOT MATCHED THEN"
                    "    INSERT (change_id, development_change_number, name, datetime, software_release_version, series)"
                    "      VALUES (source.change_id, ?, ?, ?, ?, ?);")
                try:
                    db.sql(merge_stmt, (changeset, devchgnum, "TBD", self.mapping.start_time(msg), relver, vehicle_series))
                except Exception:
                    # This error is not uncommon, that's why we are using warning instead of error.
                    log.warning("Create baseline record failed, This error is not uncommon, that's why we are using warning instead of error")
                    log.debug("TRACE", exc_info=True)
        else:
            log.debug("No development change number given, not creating 'release_baseline' record.")


class TestsuiteResultUpdate(DataMapper):
    """Update record in 'testsuite_result' with verdict etc."""

    command = "UPDATE testsuite_result SET verdict=?, status=?, end_time=? WHERE pkey = ?"

    def values(self, msg):
        """Return mappings."""
        return (
            self.mapping.verdict(msg),
            'finished',
            self.mapping.end_time(msg),
            self.mapping.uuid(msg))

    def store(self, msg):
        """If partnumbers have been added, store them as well."""
        super(TestsuiteResultUpdate, self).store(msg)
        changeset = self.mapping.changeset(msg)
        try:
            changeset = int(changeset)
        except ValueError:
            changeset = ''
        ecu = self.mapping.ecu(msg)
        partnums = self.mapping.partnums(msg)
        hwpartnums = self.mapping.hwpartnums(msg)
        uuid = self.mapping.uuid(msg)
        if partnums:
            changeset = self.mapping.changeset(msg)
            ecu = self.mapping.ecu(msg)
            with DatabaseContext() as db:
                pnix = 0
                for pn in partnums:
                    pnix += 1
                    self.add_attribute(db, uuid, 'sw_partnumber_%02d' % pnix, pn)
                    self.add_product(db, ecu, pn)
                    if changeset and isinstance(changeset, int):
                        self.add_product_baseline(db, changeset, pn)
                self.add_attribute(db, uuid, 'sw_tag', self.mapping.sw_tag(msg))
        if hwpartnums:
            changeset = self.mapping.changeset(msg)
            ecu = self.mapping.ecu(msg)
            with DatabaseContext() as db:
                pnix = 0
                for pn in hwpartnums:
                    pnix += 1
                    self.add_attribute(db, uuid, 'hw_partnumber_%02d' % pnix, pn)
                    self.add_product(db, ecu, pn)
                    if changeset and isinstance(changeset, int):
                        self.add_product_baseline(db, changeset, pn)

    def add_product(self, db, ecu, partnumber):
        """Add software part numbers, create product if not exists."""
        prod_stmt = (
            "MERGE product AS target"
            "  USING (values (?))"
            "    AS source (partnumber)"
            "    ON target.partnumber = source.partnumber"
            "  WHEN NOT MATCHED THEN"
            "    INSERT (partnumber, ecu, description, domain, type)"
            "      VALUES (source.partnumber, ?, ?, ?, ?);")
        db.sql(prod_stmt, (partnumber, ecu, '-unknown, TBD-', 'ECUSW', 'ECUSW'))

    def add_product_baseline(self, db, changeset, partnumber):
        """Connect baseline and product tables."""
        pb_stmt = (
            "MERGE product_release_baseline AS target"
            "  USING (values (?, ?))"
            "    AS source (product, release_baseline)"
            "    ON target.product = source.product"
            "      AND target.release_baseline = source.release_baseline"
            "  WHEN NOT MATCHED THEN"
            "     INSERT (product, release_baseline)"
            "        VALUES (source.product, source.release_baseline);" )
        db.sql(pb_stmt, (partnumber, changeset))


class TestcaseResultInsert(DataMapper):
    """Create new record in 'testcase_result'."""

    command = (
        "INSERT INTO testcase_result"
        "    (pkey, testsuite_result, testcase, name, start_time, status, verdict)"
        "  VALUES (?, ?, ?, ?, ?, ?, ?)")

    def values(self, msg):
        """Return mappings."""
        name = self.mapping.name(msg)
        return (
            self.mapping.uuid(msg),
            self.mapping.testsuite_result(msg),
            name,
            name,
            self.mapping.start_time(msg),
            'ongoing',
            'unknown')

    def store(self, msg):
        # Reset the routine that checks for unique test step names within a test case.
        reset_teststep_cache()
        super(TestcaseResultInsert, self).store(msg)
        with DatabaseContext() as db:
            requirement_id = self.mapping.requirement_id(msg)
            responsible = self.mapping.responsible(msg)
            testcase_name = self.mapping.name(msg)
            self.add_testcase(db, testcase_name)
            if responsible is not None:
                self.add_responsible(db, responsible, testcase_name)
            if requirement_id is not None:
                req = RequirementParser(requirement_id)
                try:
                    self.add_requirement_mapping(db, testcase_name, req.key)
                except Exception as e:
                    log.warning("Could not add link between test case and requirement.")
                    log.debug("TRACE", exc_info=True)

    def add_requirement_mapping(self, db, testcase_name, requirement_id):
        """Add mapping in table 'requirement_testcase' between testcase and requirement."""
        reqtc_merge_stmt = (
            "MERGE requirement_testcase AS target"
            "  USING (values (?, ?))"
            "    AS source (requirement, testcase)"
            "    ON target.requirement= ? AND target.testcase= ?"
            "  WHEN NOT MATCHED THEN"
            "    INSERT (requirement, testcase) VALUES (source.requirement, source.testcase);")
        db.sql(reqtc_merge_stmt, (requirement_id, testcase_name, requirement_id, testcase_name))

    def add_responsible(self, db, responsible, testcase_name):
        """Add 'author' if responsible is given"""
        db.sql("UPDATE testcase SET author = ? WHERE pkey = ?", (
            responsible, testcase_name))

    def add_testcase(self, db, testcase_name):
        """Create a record in the testcase table if not already existing."""
        tc_merge_stmt = (
            "MERGE testcase AS target"
            "  USING (values (?))"
            "    AS source (pkey)"
            "    ON target.pkey = ?"
            "  WHEN NOT MATCHED THEN"
            "    INSERT (pkey, name) VALUES (source.pkey, source.pkey);")
        db.sql(tc_merge_stmt, (testcase_name, testcase_name))


class TestcaseResultUpdate(DataMapper):
    """Update record in 'testcase_result' with verdict etc."""

    command = (
        "UPDATE testcase_result SET verdict=?, status=?, end_time=?"
        "  WHERE pkey = ?")

    def values(self, msg):
        """Return mappings."""
        return (
            self.mapping.verdict(msg),
            'finished',
            self.mapping.end_time(msg),
            self.mapping.uuid(msg))


class TeststepResult(DataMapper):
    """Create new record in 'teststep_result' including verdict since these
    results are cached."""

    command = (
        "INSERT INTO teststep_result"
        "    (testsuite_result, testcase_result, name, start_time, end_time, verdict, status)"
        "  VALUES (?, ?, ?, ?, ?, ?, ?)")

    def values(self, msg):
        """Return mappings."""
        return (
            self.mapping.testsuite_result(msg),
            self.mapping.testcase_result(msg),
            # Need to modify name to avoid that two test steps with the same
            # name creates an integrity error.
            modify_name(self.mapping.name(msg)),
            self.mapping.start_time(msg),
            self.mapping.end_time(msg),
            self.mapping.verdict(msg),
            'finished')


# Administrative tasks ==================================================={{{1
class Admin(object):
    """Perform administrative tasks."""

    # Creation has to be done in a specific order because of FK constraints
    create = OrderedDict((
        # Catalog data
        ('ecu', """
            CREATE TABLE ecu (
                name VARCHAR(16) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('label', """
            CREATE TABLE label (
                name VARCHAR(64) PRIMARY KEY NOT NULL);
            """),
        ('platform', """
            CREATE TABLE platform (
                name VARCHAR(16) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('product_type', """
            CREATE TABLE product_type (
                name VARCHAR(64) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('requirement_type', """
            CREATE TABLE requirement_type (
                name VARCHAR(64) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('test_environment', """
            CREATE TABLE test_environment (
                name VARCHAR(64) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('test_status', """
            CREATE TABLE test_status (
                name VARCHAR(16) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('testcase_tool', """
            CREATE TABLE testcase_tool (
                name VARCHAR(64) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('testsuite_type', """
            CREATE TABLE testsuite_type (
                name VARCHAR(256) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('test_verdict', """
            CREATE TABLE test_verdict (
                name VARCHAR(16) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('vehicle_project', """
            CREATE TABLE vehicle_project (
                name VARCHAR(64) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        # Base tables
        ('development_baseline', """
            CREATE TABLE development_baseline (
                change_number VARCHAR(64) PRIMARY KEY NOT NULL,
                change_id VARCHAR(64) NOT NULL,
                git_hash VARCHAR(64) NOT NULL,
                name VARCHAR(256) NOT NULL,
                repository VARCHAR(64) NOT NULL,
                branch VARCHAR(64) NOT NULL,
                datetime DATETIME NOT NULL,
                description VARCHAR(512) NULL,
                change_owner VARCHAR(64) NULL);
            """),
        ('label', """
            CREATE TABLE label (
                name VARCHAR(64) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('observer', """
            CREATE TABLE observer (
                pkey VARCHAR(64) PRIMARY KEY NOT NULL,
                name VARCHAR(256) NOT NULL,
                description VARCHAR(512) NULL,
                file_path VARCHAR(512) NULL,
            """),
        ('observer_result', """
            CREATE TABLE observer_result (
                pkey VARCHAR(64) PRIMARY KEY NOT NULL,
                activation REAL NOT NULL CHECK (0 <= activation AND activation <= 1),
                verdict INTEGER NOT NULL CHECK (0 <= verdict AND verdict <= 1),
                requirement VARCHAR(64) NOT NULL,
                testcase_result VARCHAR(256) NULL,
                testsuite_result VARCHAR(256) NULL,
                observer VARCHAR(64) NOT NULL,
                FOREIGN KEY(testcase_result, testsuite_result) REFERENCES testcase_result (pkey, testsuite_result),
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('platform_project_ecu', """
            CREATE TABLE platform_project_ecu (
                platform VARCHAR(16) NOT NULL,
                vehicle_project VARCHAR(16) NOT NULL,
                ecu VARCHAR(16) NOT NULL,
                PRIMARY KEY (platform, vehicle_project, ecu),
                FOREIGN KEY(platform) REFERENCES platform (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(vehicle_project) REFERENCES vehicle_project (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(ecu) REFERENCES ecu (name) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('product', """
            CREATE TABLE product (
                partnumber VARCHAR(64) PRIMARY KEY NOT NULL,
                type VARCHAR(64) NOT NULL,
                description VARCHAR(256) NOT NULL,
                domain VARCHAR(256) NOT NULL,
                ecu VARCHAR(16) NULL,
                FOREIGN KEY(type) REFERENCES product_type (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(ecu) REFERENCES ecu (name) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('release_baseline', """
            CREATE TABLE release_baseline (
                change_id VARCHAR(64) PRIMARY KEY NOT NULL,
                development_change_number VARCHAR(64) NULL,
                name VARCHAR(256) NOT NULL,
                datetime DATETIME NOT NULL,
                description VARCHAR(512) NULL,
                software_release_version VARCHAR(64) NOT NULL,
                series VARCHAR(16) NOT NULL,
                FOREIGN KEY(development_change_number) REFERENCES development_baseline (change_number) ON DELETE SET NULL ON UPDATE CASCADE);
            """),
        ('requirement', """
            CREATE TABLE requirement (
                pkey VARCHAR(64) PRIMARY KEY NOT NULL,
                id VARCHAR(16) NOT NULL,
                revision VARCHAR(16) NOT NULL,
                variant VARCHAR(16) NOT NULL,
                name VARCHAR(256) NULL,
                elektra_version_id VARCHAR(64) NULL,
                carweaver_version_id VARCHAR(64) NULL,
                parent VARCHAR(64) NULL,
                type VARCHAR(64) NOT NULL,
                FOREIGN KEY(parent) REFERENCES requirement (pkey) ON DELETE NO ACTION ON UPDATE NO ACTION,
                FOREIGN KEY(type) REFERENCES requirement_type (name) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('runtime_data', """
            CREATE TABLE runtime_data (
                testsuite_result VARCHAR(256) NOT NULL,
                attribute VARCHAR(64) NOT NULL,
                value VARCHAR(512) NULL,
                PRIMARY KEY (testsuite_result, attribute));
            """),
        ('software_component', """
            CREATE TABLE software_component (
                pkey VARCHAR(64) PRIMARY KEY NOT NULL,
                name VARCHAR(256) NOT NULL,
                description VARCHAR(512) NULL,
                file_path VARCHAR(512) NULL);
            """),
        ('testcase', """
            CREATE TABLE testcase (
                pkey VARCHAR(256) PRIMARY KEY NOT NULL,
                name VARCHAR(256) NULL,
                author VARCHAR(64) NULL,
                creation_date DATETIME NULL,
                modification_date DATETIME NULL,
                description VARCHAR(512) NULL,
                file_path VARCHAR(512) NULL);
            """),
        ('testcase_result', """
            CREATE TABLE testcase_result (
                pkey VARCHAR(256) NOT NULL,
                testsuite_result VARCHAR(256) NOT NULL,
                testcase VARCHAR(256) NULL,
                name VARCHAR(256) NULL,
                start_time DATETIME NULL,
                end_time DATETIME NULL,
                remark VARCHAR(512) NULL,
                measurement_file VARCHAR(512) NULL,
                verdict VARCHAR(16) NOT NULL,
                status VARCHAR(16) NOT NULL,
                PRIMARY KEY (pkey, testsuite_result),
                FOREIGN KEY(verdict) REFERENCES test_verdict (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(status) REFERENCES test_status (name) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('teststep', """
            CREATE TABLE teststep (
                testcase VARCHAR(256) NOT NULL,
                name VARCHAR(256) NOT NULL,
                author VARCHAR(64) NULL,
                creation_date DATETIME NULL,
                modification_date DATETIME NULL,
                description VARCHAR(512) NULL,
                PRIMARY KEY (testcase, name));
            """),
        ('teststep_result', """
            CREATE TABLE teststep_result (
                testsuite_result VARCHAR(256) NOT NULL,
                testcase_result VARCHAR(256) NOT NULL,
                name VARCHAR(256) NOT NULL,
                start_time DATETIME NULL,
                end_time DATETIME NULL,
                remark VARCHAR(512) NULL,
                verdict VARCHAR(16) NULL,
                status VARCHAR(16) NULL,
                PRIMARY KEY (testsuite_result, testcase_result, name),
                FOREIGN KEY(verdict) REFERENCES test_verdict (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(status) REFERENCES test_status (name) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('testsuite', """
            CREATE TABLE testsuite (
                pkey VARCHAR(256) PRIMARY KEY NOT NULL,
                name VARCHAR(256) NOT NULL,
                description VARCHAR(512) NULL,
                testcase_tool VARCHAR(64) NOT NULL,
                type VARCHAR(256) NOT NULL,
                FOREIGN KEY(testcase_tool) REFERENCES testcase_tool (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(type) REFERENCES testsuite_type (name) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('testsuite_result', """
            CREATE TABLE testsuite_result (
                pkey VARCHAR(256) PRIMARY KEY NOT NULL,
                name VARCHAR(256) NOT NULL,
                description VARCHAR(512) NULL,
                executor VARCHAR(64) NULL,
                start_time DATETIME NULL,
                end_time DATETIME NULL,
                remark VARCHAR(512) NULL,
                testsuite VARCHAR(256) NULL,
                ecu VARCHAR(16) NULL,
                vehicle_project VARCHAR(16) NULL,
                platform VARCHAR(16) NULL,
                development_baseline VARCHAR(64) NULL,
                release_baseline VARCHAR(64) NULL,
                verdict VARCHAR(16) NOT NULL,
                status VARCHAR(16) NOT NULL,
                environment VARCHAR(64) NOT NULL,
                testcase_tool VARCHAR(64) NOT NULL,
                FOREIGN KEY(ecu) REFERENCES ecu (name) ON DELETE SET NULL ON UPDATE CASCADE,
	            FOREIGN KEY(vehicle_project) REFERENCES vehicle_project (name) ON DELETE SET NULL ON UPDATE CASCADE,
	            FOREIGN KEY(platform) REFERENCES platform (name) ON DELETE SET NULL ON UPDATE CASCADE,
                FOREIGN KEY(verdict) REFERENCES test_verdict (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(status) REFERENCES test_status (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(environment) REFERENCES test_environment (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(testcase_tool) REFERENCES testcase_tool (name) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        # Link tables
        ('observer_development_baseline', """
            CREATE TABLE observer_development_baseline (
                observer VARCHAR(64) NOT NULL,
                development_baseline VARCHAR(64) NOT NULL,
                PRIMARY KEY (observer, development_baseline),
                FOREIGN KEY(observer) REFERENCES observer (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(development_baseline) REFERENCES development_baseline (change_number) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('product_release_baseline', """
            CREATE TABLE product_release_baseline (
                product VARCHAR(64) NOT NULL,
                release_baseline VARCHAR(64) NOT NULL,
                PRIMARY KEY (product, release_baseline),
                FOREIGN KEY(product) REFERENCES product (partnumber) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(release_baseline) REFERENCES release_baseline (changeset) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('requirement_development_baseline', """
            CREATE TABLE requirement_development_baseline (
                requirement VARCHAR(64) NOT NULL,
                development_baseline VARCHAR(64) NOT NULL,
                PRIMARY KEY (requirement, development_baseline),
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(development_baseline) REFERENCES development_baseline (change_number) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('requirement_ecu', """
            CREATE TABLE requirement_ecu (
                ecu VARCHAR(16) NOT NULL,
                requirement VARCHAR(64) NOT NULL,
                PRIMARY KEY (ecu, requirement),
                FOREIGN KEY(ecu) REFERENCES ecu (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('requirement_label', """
            CREATE TABLE requirement_label (
                requirement VARCHAR(64) NOT NULL,
                label VARCHAR(64) NOT NULL,
                PRIMARY KEY (requirement, label),
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(label) REFERENCES label (name) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('requirement_observer', """
            CREATE TABLE requirement_observer (
                requirement VARCHAR(64) NOT NULL,
                observer VARCHAR(64) NOT NULL,
                PRIMARY KEY (requirement, observer),
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(observer) REFERENCES observer (pkey) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('requirement_platform', """
            CREATE TABLE requirement_platform (
                platform VARCHAR(16) NOT NULL,
                requirement VARCHAR(64) NOT NULL,
                PRIMARY KEY (platform, requirement),
                FOREIGN KEY(platform) REFERENCES platform (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('requirement_software_component', """
            CREATE TABLE requirement_software_component (
                requirement VARCHAR(64) NOT NULL,
                software_component VARCHAR(64) NOT NULL,
                PRIMARY KEY (requirement, software_component),
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(software_component) REFERENCES software_component (pkey) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('requirement_testcase', """
            CREATE TABLE requirement_testcase (
                requirement VARCHAR(64) NOT NULL,
                testcase VARCHAR(256) NOT NULL,
                PRIMARY KEY (requirement, testcase),
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(testcase) REFERENCES testcase (pkey) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('requirement_type', """
            CREATE TABLE requirement_type (
                name VARCHAR(64) PRIMARY KEY NOT NULL,
                description VARCHAR(512) NULL);
            """),
        ('requirement_vehicle_project', """
            CREATE TABLE requirement_vehicle_project (
                vehicle_project VARCHAR(16) NOT NULL,
                requirement VARCHAR(64) NOT NULL,
                PRIMARY KEY (vehicle_project, requirement),
                FOREIGN KEY(vehicle_project) REFERENCES vehicle_project (name) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(requirement) REFERENCES requirement (pkey) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('software_component_development_baseline', """
            CREATE TABLE software_component_development_baseline (
                software_component VARCHAR(64) NOT NULL,
                development_baseline VARCHAR(64) NOT NULL,
                PRIMARY KEY (software_component, development_baseline),
                FOREIGN KEY(software_component) REFERENCES software_component (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(development_baseline) REFERENCES development_baseline (change_number) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('testcase_development_baseline', """
            CREATE TABLE testcase_development_baseline (
                testcase VARCHAR(256) NOT NULL,
                development_baseline VARCHAR(64) NOT NULL,
                PRIMARY KEY (testcase, development_baseline),
                FOREIGN KEY(testcase) REFERENCES testcase (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(development_baseline) REFERENCES development_baseline (change_number) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('testcase_release_baseline', """
            CREATE TABLE testcase_release_baseline (
                testcase VARCHAR(256) NOT NULL,
                release_baseline VARCHAR(64) NOT NULL,
                PRIMARY KEY (testcase, release_baseline),
                FOREIGN KEY(testcase) REFERENCES testcase (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(release_baseline) REFERENCES release_baseline (changeset) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ('testsuite_testcase', """
            CREATE TABLE testsuite_testcase (
                testsuite VARCHAR(256) NOT NULL,
                testcase VARCHAR(256) NOT NULL,
                PRIMARY KEY (testsuite, testcase),
                FOREIGN KEY(testsuite) REFERENCES testsuite (pkey) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY(testcase) REFERENCES testcase (pkey) ON DELETE CASCADE ON UPDATE CASCADE);
            """),
        ))

    test_status_values = (
        ('unknown',     "Unknown job state (default state)."),
        ('queued',      "The job has been queued."),
        ('allocated',   "Resources have been allocated, but the job has not yet started."),
        ('ongoing',     "The job is running."),
        ('finished',    "The job is finished."),
        ('disabled',    "The job has been disabled."))

    test_verdict_values = (
        ('unknown',     "No verdict has been given."),
        ('passed',      "The test passed."),
        ('failed',      "The test failed."),
        ('errored',     "There was an error that prevented the test from running."),
        ('skipped',     "The test has been skipped."),
        ('aborted',     "The test was aborted."))

    framework_values = (
        ('unknown',     "Unknown framework"),
        ('AutomationDesk', "dSPACE AutomationDesk"),)

    environment_values = (
        ('HIL',     "Hardware-In-the-Loop testing"),)

    reqtype_values = (
        ('srd', 'System requirement'),)

    def init(self):
        self.create_tables()
        self.add_catalog_data()

    def create_tables(self):
        with DatabaseContext() as db:
            for tablename in self.create:
                self.create_table(db, tablename)

    def create_table(self, db, tablename):
        log.info("Creating table '{}'.".format(tablename))
        db.sql(self.create[tablename])

    def drop_tables(self):
        with DatabaseContext() as db:
            for tablename in self.create:
                self.drop_table(db, tablename)

    def drop_table(self, db, tablename):
        log.info("Dropping table '{}'.".format(tablename))
        db.sql("DROP TABLE {}".format(tablename))

    def add_catalog_data(self):
        with DatabaseContext() as db:
            for name, desc in self.test_status_values:
                try:
                    self.add_test_status(db, name, desc)
                except Exception as e:
                    log.warning(e)
            for name, desc in self.test_verdict_values:
                try:
                    self.add_test_verdict(db, name, desc)
                except Exception as e:
                    log.warning(e)
            for name, desc in self.environment_values:
                try:
                    self.add_environment(db, name)
                except Exception as e:
                    log.warning(e)
            for name, desc in self.framework_values:
                try:
                    self.add_framework(db, name)
                except Exception as e:
                    log.warning(e)
            for name, desc in self.reqtype_values:
                try:
                    self.add_reqtype(db, name)
                except Exception as e:
                    log.warning(e)

    def add_test_status(self, db, name, description=None):
        """INSERT catalog data for test_status table"""
        log.info("Adding test_status '{}'.".format(name))
        if description is None:
            db.sql("INSERT INTO test_status (name) VALUES (?)", (name,))
        else:
            db.sql("INSERT INTO test_status (name, description) VALUES (?, ?)", (name, description))

    def add_test_verdict(self, db, name, description=None):
        """INSERT catalog data for test_verdict table"""
        log.info("Adding test_verdict '{}'.".format(name))
        if description is None:
            db.sql("INSERT INTO test_verdict (name) VALUES (?)", (name,))
        else:
            db.sql("INSERT INTO test_verdict (name, description) VALUES (?, ?)", (name, description))

    def add_environment(self, db, name):
        log.info("Adding test_environment '{}'.".format(name))
        db.sql("INSERT INTO test_environment (name) VALUES (?)", (name,))

    def add_framework(self, db, name):
        log.info("Adding testcase_tool '{}'.".format(name))
        db.sql("INSERT INTO testcase_tool (name) VALUES (?)", (name,))

    def add_reqtype(self, db, name):
        log.info("Adding requirement_type '{}'.".format(name))
        db.sql("INSERT INTO requirement_type (name) VALUES (?)", (name,))


class TestStepNameGenerator(dict):
    """Try to solve the problem with test steps that have the same names within
    the same test case.  The first time a test step is run it will keep its
    name. The next time the same test step name occurs, then it will have a
    number appended to its name."""
    def get_name(self, name):
        """If name has alredy been used, then return 'Name [instance number]'."""
        if name in self:
            self[name] += 1
            return "{} [{}]".format(name, self[name])
        else:
            self[name] = 0
            return name

try:
    TESTSTEP_NAME_GENERATOR
except NameError:
    TESTSTEP_NAME_GENERATOR = TestStepNameGenerator()


# Functions =============================================================={{{1
def admin():
    """Return "Admin" object for database administrative tasks."""
    return Admin()


def init():
    """Create all tables and add catalog data."""
    admin().init()


def connection_factory():
    """Return connection factory as configured in 'configuration' object."""
    return ConnectionFactory(CONFIG.enabled, CONFIG.dbtype, *CONFIG.connstr)


def modify_name(name):
    """Return a modified name if the test execution has used the same name for
    the test step earlier. Unfortunately it's possible to create test steps
    with exactly the same names in AutomationDesk."""
    return TESTSTEP_NAME_GENERATOR.get_name(name)


def reset_teststep_cache():
    """Reset the TESTSTEP_NAME_GENERATOR by clearing its contents."""
    TESTSTEP_NAME_GENERATOR.clear()


def set_config(enabled=None, dbtype=None, connstr=None):
    if enabled is not None:
        CONFIG.enabled = bool(enabled)
    if dbtype is not None:
        CONFIG.dbtype = dbtype
    if connstr is not None:
        CONFIG.connstr = connstr


def store_data(data,share_activity):
    """Store data (a mapping)."""
    if 'type' in data and data['type'] == 'baseline':
        # DO NOTHING right now, baseline messages don't contain anything interesting
        pass
    elif 'taskId' in data:
        # Tasks (test cases and test steps)
        if 'parentTaskId' in data:
            # *** TEST STEP ***
            # The message was a create message for a test step (task with parent task)
            TeststepResult(TeststepResultMapping()).store(data)
        else:
            tcase_map = TestcaseResultMapping()
            # *** TEST CASE ***
            if 'verdict' in data:
                # The message was an update message for a test case (task)
                TestcaseResultUpdate(tcase_map).store(data)
            else:
                # The message was a create message for a test case (task)
                TestcaseResultInsert(tcase_map).store(data)
    elif 'activityId' in data:
        # *** TEST SUITE ***
        # Activity = test suite
        tsuite_map = TestsuiteResultMapping()
        if 'verdict' in data:
            # The message was an update message for a test suite (activity)
            TestsuiteResultUpdate(tsuite_map).store(data)
        elif ('productId' or 'productIds') in data or share_activity:
            TestsuiteResultInsert(tsuite_map).store(data)

# modeline ==============================================================={{{1
# vim: set fdm=marker:
# eof
