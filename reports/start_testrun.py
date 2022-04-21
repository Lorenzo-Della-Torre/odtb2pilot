from manage import handle_rigs
from hilding.testrunner import nightly
from reports.did_report import did_report
from reports.logs_to_html import logs_to_html
from reports.testcase_picker import testcase_picker
from hilding.rig import handle_rigs

def run():
    """

    """

    try:
        # Executes the smoke tests and returns True/False
        #smoke_tests = ['Test1', 'Test2', 'Test3']
        #smoke_test_result = nightly(smoke_tests)
        smoke_test_result = True # For testing

        if smoke_test:
            # Creates testscripts_auto.lst Need xml and script_folder (matching)
            swrs = "NOTE-SWRS-33754905-01-5.xml"
            scriptfolder = "$TESTREPO/test_folder"
            testscripts = testcase_picker(swrs, scriptfolder)
            #testscripts = /autotest/testcase_picker.py --swrs NOTE-SWRS-33754905-01-5.xml --scriptfolder $TESTREPO/test_folder

            handle_rigs(update) #manage.py rigs --update
            #manage.py sddb

            # Uses testscripts_auto.lst from testcase_picker
            # Executes all testscripts and creates logs
            testrun_results = nightly(testscripts)

            # Creates ecu_info file for log_report and did_report.html
            ecu_info = did_report()

            # Generate test stats plot graph for log_report
            #/autotest/local_stats_plot.py --resultfolder . --outplot stats_plot

            # Generate log_report.html
            out_html_file = "$PWD/index.html"
            reqcsv = "req_bsw.csv"
            logs_to_html(ecu_info, testrun_results, out_html_file, reqcsv)
            #/projects/project_template/automated_testrun/logs_to_html.py --logs $PWD --reqcsv $ODTBPROJPARAM/req_bsw.csv --script_folder $TESTREPO/ --outfile $PWD/index.html
        #else:
            # Generate log report with fail
            #logs_to_html(ecu_info)
            #/projects/project_template/automated_testrun/logs_to_html.py --logs $PWD --reqcsv $ODTBPROJPARAM/req_bsw.csv --script_folder $TESTREPO/ --outfile $PWD/index.html

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
