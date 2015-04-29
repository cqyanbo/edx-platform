"""
Tests of re-verification service.
"""

import ddt

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from course_modes.tests.factories import CourseModeFactory
from student.tests.factories import UserFactory
from verify_student.models import VerificationCheckpoint, VerificationStatus
from verify_student.services import ReverificationService


@ddt.ddt
class TestReverificationService(ModuleStoreTestCase):
    """
    Tests for the re-verification service.
    """

    def setUp(self):
        super(TestReverificationService, self).setUp()

        self.user = UserFactory.create(username="rusty", password="test")
        course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.course_key = course.id
        CourseModeFactory(
            mode_slug="verified",
            course_id=self.course_key,
            min_price=100,
        )
        self.item = ItemFactory.create(parent=course, category='chapter', display_name='Test Section')

    @ddt.data("final_term", "mid_term")
    def test_start_verification(self, checkpoint_name):
        """
        Test the 'start_verification' service method. If checkpoint exists for
        a specific course then return the checkpoint otherwise created that
        checkpoint.
        """

        reverification_service = ReverificationService()
        reverification_service.start_verification(unicode(self.course_key), checkpoint_name, self.item.location)
        expected_url = (
            '/verify_student/reverify'
            '/{course_key}'
            '/{checkpoint_name}'
            '/{usage_id}/'
        ).format(course_key=unicode(self.course_key), checkpoint_name=checkpoint_name, usage_id=self.item.location)

        self.assertEqual(
            expected_url,
            reverification_service.start_verification(unicode(self.course_key), checkpoint_name, self.item.location)
        )

    def test_get_status(self):
        """
        Check if the user has any verification attempt for a given 'checkpoint'
        and 'course_id'.
        """

        checkpoint_name = 'final_term'
        reverification_service = ReverificationService()
        self.assertIsNone(reverification_service.get_status(self.user.id, unicode(self.course_key), checkpoint_name))

        checkpoint_obj = VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_key), checkpoint_name=checkpoint_name
        )
        status = VerificationStatus.VERIFICATION_STATUS_CHOICES.submitted
        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status=status)
        self.assertEqual(
            reverification_service.get_status(self.user.id, unicode(self.course_key), checkpoint_name),
            status
        )

    def test_get_attempts(self):
        """
        Check verification attempt against a user for a given 'checkpoint' and
        'course_id'.
        """

        checkpoint_name = 'final_term'
        reverification_service = ReverificationService()
        self.assertEqual(
            reverification_service.get_attempts(self.user.id, unicode(self.course_key), checkpoint_name, location_id=''),
            0
        )

        # now create a checkpoint and add user's entry against it then test
        # that the 'get_attempts' service method returns count accordingly
        checkpoint_obj = VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_key), checkpoint_name=checkpoint_name
        )
        status = VerificationStatus.VERIFICATION_STATUS_CHOICES.submitted
        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status=status)
        self.assertEqual(
            reverification_service.get_attempts(self.user.id, unicode(self.course_key), checkpoint_name, location_id=''),
            1
        )
