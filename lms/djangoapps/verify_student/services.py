"""
Implementation of "reverification" service to communicate with Reverification XBlock
"""

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from verify_student.models import VerificationCheckpoint, VerificationStatus


class ReverificationService(object):
    """
    Reverification XBlock service
    """

    def get_status(self, user_id, course_id, related_assessment):
        """
        Get verification attempt status against a user for a given 'checkpoint'
        and 'course_id'.

        Args:
            user_id(str): User Id string
            course_id(str): A string of course id
            related_assessment(str): Verification checkpoint name

        Returns:
            Verification Status string if any attempt submitted by user else None
        """
        course_key = CourseKey.from_string(course_id)
        try:
            checkpoint_status = VerificationStatus.objects.filter(
                user_id=user_id,
                checkpoint__course_id=course_key,
                checkpoint__checkpoint_name=related_assessment
            ).latest()
            return checkpoint_status.status
        except ObjectDoesNotExist:
            return None

    def start_verification(self, course_id, related_assessment, item_id):
        """
        Create re-verification link against a verification checkpoint.

        Args:
            course_id(str): A string of course id
            related_assessment(str): Verification checkpoint name

        Returns:
            Re-verification link
        """
        course_key = CourseKey.from_string(course_id)
        VerificationCheckpoint.objects.get_or_create(course_id=course_key, checkpoint_name=related_assessment)
        re_verification_link = reverse(
            'verify_student_incourse_reverify',
            args=(
                unicode(course_key),
                unicode(related_assessment),
                unicode(item_id)
            )
        )
        return re_verification_link

    def get_attempts(self, user_id, course_id, related_assessment, location_id):
        """
        Get re-verification attempts against a user for a given 'checkpoint'
        and 'course_id'.

        Args:
            user_id(str): User Id string
            course_id(str): A string of course id
            related_assessment(str): Verification checkpoint name
            location_id(str): Reverification XBlock's location in courseware

        Returns:
            Number of re-verification attempts of a user
        """
        course_key = CourseKey.from_string(course_id)
        return VerificationStatus.objects.filter(
            user_id=user_id,
            checkpoint__course_id=course_key,
            checkpoint__checkpoint_name=related_assessment,
            checkpoint__location_id=location_id,
            status=VerificationStatus.VERIFICATION_STATUS_CHOICES.submitted
        ).count()
