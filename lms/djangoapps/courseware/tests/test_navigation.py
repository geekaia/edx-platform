"""
This test file will run through some LMS test scenarios regarding access and navigation of the LMS
"""
import time
from django.conf import settings

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from courseware.tests.helpers import LoginEnrollmentTestCase, check_for_get_code
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from courseware.tests.factories import GlobalStaffFactory


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestNavigation(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Check that navigation state is saved properly.
    """

    STUDENT_INFO = [('view@test.com', 'foo'), ('view2@test.com', 'foo')]

    def setUp(self):

        self.test_course = CourseFactory.create(display_name='Robot_Sub_Course')
        self.course = CourseFactory.create(display_name='Robot_Super_Course')
        self.chapter0 = ItemFactory.create(parent_location=self.course.location,
                                           display_name='Overview')
        self.chapter9 = ItemFactory.create(parent_location=self.course.location,
                                           display_name='factory_chapter')
        self.section0 = ItemFactory.create(parent_location=self.chapter0.location,
                                           display_name='Welcome')
        self.section9 = ItemFactory.create(parent_location=self.chapter9.location,
                                           display_name='factory_section')
        self.unit0 = ItemFactory.create(parent_location=self.section0.location,
                                        display_name='New Unit')

        # Create student accounts and activate them.
        for i in range(len(self.STUDENT_INFO)):
            email, password = self.STUDENT_INFO[i]
            username = 'u{0}'.format(i)
            self.create_account(username, email, password)
            self.activate_user(email)

        self.staff_user = GlobalStaffFactory()

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=1)
    def test_inactive_session_timeout(self):
        """
        Verify that an inactive session times out and redirects to the
        login page
        """
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)

        # make sure we can access courseware immediately
        resp = self.client.get(reverse('dashboard'))
        self.assertEquals(resp.status_code, 200)

        # then wait a bit and see if we get timed out
        time.sleep(2)

        resp = self.client.get(reverse('dashboard'))

        # re-request, and we should get a redirect to login page
        self.assertRedirects(resp, settings.LOGIN_REDIRECT_URL + '?next=' + reverse('dashboard'))

    def test_redirects_first_time(self):
        """
        Verify that the first time we click on the courseware tab we are
        redirected to the 'Welcome' section.
        """
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.course.id.to_deprecated_string()}))

        self.assertRedirects(resp, reverse(
            'courseware_section', kwargs={'course_id': self.course.id.to_deprecated_string(),
                                          'chapter': 'Overview',
                                          'section': 'Welcome'}))

    def test_redirects_second_time(self):
        """
        Verify the accordion remembers we've already visited the Welcome section
        and redirects correpondingly.
        """
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        self.client.get(reverse('courseware_section', kwargs={
            'course_id': self.course.id.to_deprecated_string(),
            'chapter': 'Overview',
            'section': 'Welcome',
        }))

        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.course.id.to_deprecated_string()}))

        self.assertRedirects(resp, reverse(
            'courseware_chapter',
            kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'chapter': 'Overview'
            }
        ))

    def test_accordion_state(self):
        """
        Verify the accordion remembers which chapter you were last viewing.
        """
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        # Now we directly navigate to a section in a chapter other than 'Overview'.
        check_for_get_code(self, 200, reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'chapter': 'factory_chapter',
                'section': 'factory_section'
            }
        ))

        # And now hitting the courseware tab should redirect to 'factory_chapter'
        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.course.id.to_deprecated_string()}))

        self.assertRedirects(resp, reverse('courseware_chapter',
                                           kwargs={'course_id': self.course.id.to_deprecated_string(),
                                                   'chapter': 'factory_chapter'}))

    def test_incomplete_course(self):
        email = self.staff_user.email
        password = "test"
        self.login(email, password)
        self.enroll(self.test_course, True)

        test_course_id = self.test_course.id.to_deprecated_string()

        check_for_get_code(
            self, 200,
            reverse(
                'courseware',
                kwargs={'course_id': test_course_id}
            )
        )

        section = ItemFactory.create(
            parent_location=self.test_course.location,
            display_name='New Section'
        )
        check_for_get_code(
            self, 200,
            reverse(
                'courseware',
                kwargs={'course_id': test_course_id}
            )
        )

        subsection = ItemFactory.create(
            parent_location=section.location,
            display_name='New Subsection'
        )
        check_for_get_code(
            self, 200,
            reverse(
                'courseware',
                kwargs={'course_id': test_course_id}
            )
        )

        ItemFactory.create(
            parent_location=subsection.location,
            display_name='New Unit'
        )
        check_for_get_code(
            self, 302,
            reverse(
                'courseware',
                kwargs={'course_id': test_course_id}
            )
        )
