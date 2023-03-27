from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        labels = {
            'text': 'Tекст поста',
            'group': 'Группа',
        }
        help_texts = {'text': 'Введите текст',
                      'group': 'Выберите группу из списка'
                      }
