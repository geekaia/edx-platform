__author__ = 'geekaia'
# -*- coding: utf-8 -*-

from experiments.models import *
from courseware import grades

from courseware.courses import get_course_with_access
from django.http import Http404
from courseware.access import has_access


# def progress(request, course_id, student_id=None):
#     """
#     Wraps "_progress" with the manual_transaction context manager just in case
#     there are unanticipated errors.
#     """
#     with grades.manual_transaction():
#         return _progress(request, course_id, student_id)

# @cache_control(no_cache=True, no_store=True, must_revalidate=True)
# @transaction.commit_manually

def progress(request, course_id, student_id):
    """
    Unwrapped version of "progress".
courseware_summary
    User progress. We show the grade bar and every problem score.

    Course staff are allowed to see the progress of students in their class.
    """

    print " -------------- "
    print "Request.user: ", request.user, " Course id: ",  course_id, " Student id: ", student_id
    print " -------------- "

    course = get_course_with_access(request.user, course_id, 'load', depth=None)
    print "PEGUEI O CURSO"
    staff_access = has_access(request.user, course, 'staff')

    if not staff_access:
            raise Http404

    if student_id is None or student_id == request.user.id:
        # always allowed to see your own profile
        student = request.user
    else:
        # Requesting access to a different student's profile
        if not staff_access:
            raise Http404
        student = User.objects.get(id=int(student_id))

    # NOTE: To make sure impersonation by instructor works, use
    # student instead of request.user in the rest of the function.

    # The pre-fetching of groups is done to make auth checks not require an
    # additional DB lookup (this kills the Progress page in particular).
    student = User.objects.prefetch_related("groups").get(id=student.id)

    print "PEGANDO O ...COURSEWARE SUMMARY "


    try:
        courseware_summary = grades.progress_summary(student, request, course)

        print
        print
        print
        print
        print "Informações: "
        # print "Usuario: ", courseware_summary['sections']
        # courseware_summary




        print "TAMANHO: ", len(courseware_summary)
        print
        print
        print
        print
    except:
        print "GRADE SUMMARY IS NONE with Exception"
        courseware_summary = None



    # try:
    #     grade_summary = grades.grade(student, request, course)
    # except:
    #     print "Grade: setting none "
    #     grade_summary = None

    print "TAMANHO 2: ", len(courseware_summary)

    return courseware_summary #, grade_summary

