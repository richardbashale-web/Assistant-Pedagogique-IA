from django.db import models

class Course(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    professeur = models.ForeignKey(
        'users.Professor',
        on_delete=models.CASCADE,
        related_name='courses',
        null=True,
        blank=True,
    )
    faculte = models.ForeignKey('users.Faculty', on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    promotions = models.JSONField(default=list, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre


class CourseNote(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='notes')
    professor = models.ForeignKey('users.Professor', on_delete=models.SET_NULL, null=True, blank=True, related_name='course_notes')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default='')
    attachment = models.FileField(upload_to='course_notes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Note: {self.title} ({self.course.titre})"
