"""
Contains views for the sherlocked app.
"""

from django.shortcuts import HttpResponse, render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from sherlocked2019 import settings

from userAuth.models import Player
from .models import Question

from datetime import tzinfo, timedelta, datetime


@login_required
def dashboard(request):

    """
    Player dashboard containing the basic info like
    the level user is at.
    """

    player = Player.objects.get(username=request.user.username)
    return HttpResponse("Hello, {}. This is the dashboard. You are at level {}"\
        .format(player.username, player.level))

@login_required(login_url='/login')
def play(request):

    """
    This method will render the question according to
    the no. of question a player have solved. The submit url
    also redirects to this question.
    """
    if datetime.now() < settings.START_TIME:
        return render(request,'sherlocked/wait.html')
     
    player = Player.objects.get(username=request.user.username)
    
    tz_info = player.unlock_time.tzinfo
    time_left = (player.unlock_time - datetime.now(tz_info)).total_seconds()

    # Check for winning condition
    if player.level == Question.objects.all().count() + 1:
        return redirect("winner")
    
    # print("Time left = ", time_left)
    if time_left >= 0:
        # Time is left until the user can access the next question
        return render(
            request,
            'sherlocked/ticking.html',
            {'time_left': time_left}
        )

    question = Question.objects.get(question_level=player.level)

    context = {
        'question': question,
    }

    return render(
        request,
        'sherlocked/play.html',
        context
    )

def submit(request):

    """
    This method is called after a user submits the answer.
    The answer gets validated through this method and if the
    answer is correct the player's level is increased.
    """

    if request.method == 'POST':

        is_correct = 'false'
        response_text = 'Wrong Answer! Please try again!'

        player = Player.objects.get(username=request.user.username)
        question = Question.objects.get(question_level=player.level)

        if question.answer.lower() == str(request.POST.get("answer")):
            # Increment the level of player if last question is not reached
            player.level = player.level + 1

            # Increment the amount of time the user needs to wait
            # to move on to the next question.
            player.unlock_time = datetime.now() + question.wait_duration
            player.last_solved = datetime.now()
            player.save()

            is_correct = 'true'
            response_text = 'Correct Answer!'

        response = {
            'isCorrect': is_correct,
            'responseText': response_text,
        }

        return JsonResponse(response)
    return redirect("play")

def leaderboard(request):
    """
    Display a leaderboard.
    The player who has solved the most number of questions is at top.
    The tie is broken in favor of the player who solved first.
    """

    players_list = Player.objects.order_by("-level", "last_solved")\
        .filter(is_superuser=False)[:30]
    # paginator = Paginator(players_list, 10)
    
    # page = request.GET.get('page')
    # players = paginator.get_page(page)

    # try:
    #     players = paginator.page(page)
    # except PageNotAnInteger:
    #     players = paginator.page(1)
    # except EmptyPage:
    #     players = paginator.page(paginator.num_pages)
    
    return render(
        request,
        'sherlocked/leaderboard.html',
        {'players': players_list}
    )
#TODo: Make a Winner Template
@login_required
def winner(request):

    player = Player.objects.get(username=request.user.username)
    if player.level == Question.objects.all().count() + 1:
        return HttpResponse("You win! Yay! Give yourself a pat on the back.")
    else:
        return redirect("play")
