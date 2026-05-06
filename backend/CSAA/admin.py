from django.contrib import admin

from CSAA.models import Classification, Thing, Tag, User, Comment, Lesson

admin.site.register(Classification)
admin.site.register(Tag)
admin.site.register(Thing)
admin.site.register(User)
admin.site.register(Lesson)
admin.site.register(Comment)
