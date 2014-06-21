# -*- coding: utf-8 -*-

from collections import defaultdict
from django.http import HttpResponse
import csv
import sys

from experiments.models import *
from student.models import CourseEnrollment
from student.views import course_from_id, single_course_reverification_info
from utils import progress
from student.models import UserProfile
from django.contrib.auth.decorators import login_required



@login_required
def expAnalise(request, course_id,  idExp):


    # Requerimentos ....

    # Pegar o UserID de todos os usuarios que participaram do experimento User Choice
    # Somar o UserID para as opções A e B
    # Calcular os gráficos de Barras com Intervalo de Confiança
    # Plotar T-test e outros Testes
    # Verificar se o usuario
    print
    print
    print
    print "Request USERS: ", request.user
    print
    print


    # Pega o Grading de acordo com o UserID do usuario
    # primeiro tenho que pegar os registros deste experimento



    try:
        # Pega os experimento
        exp = ExperimentDefinition.objects.get(id=int(idExp))


        print " Fiz a primeira parte"
        # Pega todos os usuarios do experimento
        usuariosParticipantes = UserChoiceExperiment.objects.filter(experimento=exp)


        # if not has_course_access(request.user, exp.course.split('/')[0].replace('.', '/')):
        #         raise PermissionDenied()


        print "Len ", len(usuariosParticipantes)

        # A sugestao e criar outro relatorio parecido
        # print todos os usuarios
        # TotalScoreA = [] # Quantidade de acertos de Envelopar por usuario e por Subsecao
        # TotalScoreApossibleA = [] # Quant. total de questoes getScore pega isso
        TotalUsersA = 0 # OK -- Funciona
        ScoresPorquestaoA=[]  # OK -- ja funciona
        UserAProfile=[] # OK -- ja funciona
        exercInfoA=[] # Tem que envelopar igual ao PorquestaoA

        # TotalScoreB = []
        # TotalScorePossibleB = []
        TotalUsersB = 0
        ScoresPorQuestaoB=[]
        UserBProfile=[]
        exercInfoB=[]


        for usuario in usuariosParticipantes:

            # if usuario.userStudent.username != 'staff':
            #     continue

            print "Usuario: ", usuario.userStudent, " versionExp: ", usuario.versionExp.sectionExp, "Curso id: ", usuario.versionExp.sectionExp.split('/')[0].replace('.','/')
            print "Exp URL: ", usuario.versionExp.sectionExp_url
            # request.user = usuario.userStudent
            # course = get_course_with_access(request.user, usuario.versionExp.sectionExp.split('/')[0].replace('.', '/'), 'load', depth=None)
            # request.user =
            # request.user = usuario.userStudent

            # with grades.manual_transaction():
            print "Request.user: ", request.user, "Curso: ", usuario.versionExp.sectionExp.split('/')[0].replace('.', '/')

            # course = get_course_by_id(usuario.versionExp.sectionExp.split('/')[0].replace('.', '/'), depth=None)

            # print "PEGUEI O CURSO "

            # student = User.objects.prefetch_related("groups").get(id=usuario.userStudent.id)
            # print "GET GET GROUPS STUDENTS"


            # requestcp = request.GET.copy()
            # requestcp.user = usuario.userStudent


            courseware_summary = None

            # Tem que pegar o Score de um módulo específico
            try:
                courseware_summary = progress(request, course_id, usuario.userStudent.id)

            except:
                courseware_summary = None


            usrprofl=[]

            # Get information about the user
            try:

                userprofile = UserProfile.objects.get(user=usuario.userStudent)
                usrprofl.append(userprofile.user.__unicode__())
                usrprofl.append(userprofile.location)
                usrprofl.append(userprofile.city)
                usrprofl.append(userprofile.country.__unicode__())
                usrprofl.append(userprofile.gender)
                usrprofl.append(userprofile.language)
                usrprofl.append(userprofile.level_of_education)
                usrprofl.append(userprofile.year_of_birth)

            except:
                print "Exceção ao pegar o profile do usuario"



            # Agora tem que pegar os dados de um usuário em específico e jogar em uma variavel GlobalA GlobalB para este experimento

            # if courseware_summary:
            print "EU CHEGUEI AQUIIIIIIIIIIIIII", len(courseware_summary)

            for chapter in courseware_summary:
                print "usuario.versionExp.sectionExp_url: ", usuario.versionExp.sectionExp_url
                print "chapter url: ", chapter['url_name']

                if usuario.versionExp.sectionExp_url == chapter['url_name']:
                    print "Pega se for igual aos dados do usuario ???? "
                    earned = []
                    total = []

                    exercInfo=[]
                    #
                    # TotalScoreAUser = [] # Quantidade de acertos de A Necessita envelopar User e Subsection
                    # TotalScoreApossibleAUser = [] # Quant. total de questoes getScore pega isso
                    # TotalUsersAUser = 0
                    ScoresPorquestaoAUser=[]
                    ScoresPorquestaoBUser=[]

                    # exercInfoAUser=[]

                    # UserAProfileUser=[]
                    exercInfoAUser=[]
                    exercInfoBUser=[]



                    if usuario.versionExp.version == 'A':
                        TotalUsersA = TotalUsersA + 1
                    else:
                        TotalUsersB = TotalUsersB + 1



                    for section in chapter['sections']:
                        earned.append(section['section_total'].earned)
                        total.append(section['section_total'].possible)
                        # info = section['inforExerc'].reverse()
                        # info.reverse()
                        exercInfo.append(section['inforExerc'])
                        print "------------------->>>>>>>>>>>>>>>>>>>>>>>>>"
                        print "SECTION NAME: "
                        print "Usuario: ", usuario.userStudent
                        print "earned: ", section['section_total'].earned
                        print "possible: ", section['section_total'].possible

                        print "Information exercicio reverso: ", section['inforExerc']
                        print "----------------------------->>>>>>>>>>>>>>>"
                        print "VERSAOOOOOOOOOOOOOOOO: ", usuario.versionExp.version


                        if usuario.versionExp.version == 'A':

                            exercInfoAUser.append(exercInfo)

                            if len(section['scores']) > 0:
                                # Falta os Scores de cada exercício
                                exercicio = 1
                                sectionExec = []

                                # print "|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||"
                                # print "Usuario: ", usuario.userStudent
                                # print "Scores: ", section['scores']
                                # print "|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||"
                                for UserID in section['scores']:
                                    SCORE = []
                                    SCORE.append(exercicio) # numero do exercicio
                                    SCORE.append(UserID.earned) # o Quanto conseguiu
                                    SCORE.append(UserID.possible) # Maximo possivel
                                    exercicio+=1
                                    sectionExec.append(SCORE)


                                ScoresPorquestaoAUser.append(sectionExec)


                        else:
                            # TotalScoreB.append(earned)
                            # TotalScorePossibleB.append(total)
                            exercInfoBUser.append(exercInfo)


                            if len(section['scores']) > 0:
                                # Falta os Scores de cada exercício
                                exercicio = 1
                                sectionExec=[]
                                for UserID in section['scores']:
                                    SCORE = []
                                    SCORE.append(exercicio) # numero do exercicio
                                    SCORE.append(float(UserID.earned)) # o Quanto conseguiu
                                    SCORE.append(UserID.possible) # Maximo possivel
                                    exercicio+=1
                                    sectionExec.append(SCORE)


                                ScoresPorquestaoBUser.append(sectionExec)

                    if usuario.versionExp.version == 'A':
                        # print "Score User: ", ScoresPorquestaoAUser
                        ScoresPorquestaoA.append(ScoresPorquestaoAUser)
                        UserAProfile.append(usrprofl)
                        exercInfoA.append(exercInfoAUser)
                        # TotalScoreA.append(TotalScoreAUser)
                    else:
                        ScoresPorQuestaoB.append(ScoresPorquestaoBUser)
                        UserBProfile.append(usrprofl)
                        exercInfoB.append(exercInfoBUser)


                else:
                    print "IS NOT EQUAL... .PULA!!! "



        print "<<<< -------------------------- >>>>> "
        print "RESULTADO FINAL"
        print
        print

        # print "TotalScoreA: ", TotalScoreA # Quantidade de acertos de A
        # print "TotalScoreApossibleA = ", TotalScoreApossibleA # Quant. total de questoes getScore pega isso
        print "TotalUsersA = ", TotalUsersA
        print "UserAProfile", UserAProfile
        print "ScoresPorquestaoA: ", ScoresPorquestaoA
        print "Exerc Info(tentativas e valores digitados) A : ", exercInfoA

        print
        print


        # print "TotalScoreB: ", TotalScoreB # Quantidade de acertos de A
        # print "globalB_Total = ", TotalScorePossibleB # Quant. total de questoes getScore pega isso
        print "TotalUsersB = ", TotalUsersB
        print "UserBProfile", UserBProfile
        print "ScoresPorQuestaoB", ScoresPorQuestaoB
        print "Exerc Info(tentativas e valores digitados) B : ", exercInfoB
        print
        print



        quant=0
        print "firstVal: ", UserAProfile[quant][0] # , UserAProfile[quant][1], UserAProfile[quant][2], UserAProfile[quant][4], UserAProfile[quant][5], UserAProfile[quant][6]

        if UserAProfile[quant][0]==u'':
            print "é vazio"
        else:
            print "nao e vazio"


        try:
            questoesA = len(ScoresPorquestaoA)/TotalUsersA
        except:
            print "len(ScoresPorquestaoA): ", len(ScoresPorquestaoA), " A ", TotalUsersA
            questoesA = 0

        print "QuantQuests A: ", questoesA


        try:
            questoesB = len(ScoresPorQuestaoB)/TotalUsersB
        except:
            print "len(ScoresPorQuestaoB):", len(ScoresPorQuestaoB), "totB: ", TotalUsersB
            questoesB = 0

        print "QuantQuests B: ", questoesB

        # Gera um arquivo CSV a partir dos dados coletados do aluno
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio2.csv"'

        writer = csv.writer(response)

        quant = 0
        writer.writerow(['arm',
                         'section',
                         'Questao',
                         'ScoreObtido',
                         'MaxScore',
                         'usuario',
                         'location',
                         'city',
                         'country',
                         'gender',
                         'language',
                         'level_of_education',
                         'year_of_birth',
                         'tentativas',
                         'Resposta' ,'Historico Resps'])


        # Ordem print -- Quant usuarios, sections -- exerciciios dos usuarios

        for UserID in range(0, TotalUsersA):
            userResps = ScoresPorquestaoA[UserID]
            tentValQuest = exercInfoA[UserID][0]
            profUser = UserAProfile[UserID]

            print
            print
            print "Numero sections: ", len(userResps)
            print "tentValQuest: ", len(tentValQuest)
            print "userResps: ", userResps
            print "tentValQuest: ", tentValQuest
            print
            print

            lop=0
            # Faz a iteração pela quantidade de Sections
            for sec in range(0, len(userResps)):

                questoesSection = userResps[sec]
                tentValQuestSection = tentValQuest[sec]

                print
                print "questoesSection: ", questoesSection
                print "Tamanho: ", len(questoesSection)
                print "tentValQuestSection: ", tentValQuestSection
                print


                # print "Section: ", sec, " questoes section: ", questoesSection, " tentValQuestSection: ", tentValQuestSection


                for quest in range(0, len(questoesSection)):
                    print 'A', int(sec)+1,  int(quest)+1,  toUTF8(questoesSection[quest][0]), toUTF8(questoesSection[quest][1]), toUTF8(questoesSection[quest][2]), toUTF8(profUser[0]), toUTF8(profUser[1]), toUTF8(profUser[2]), toUTF8(profUser[3]), toUTF8(profUser[4]), toUTF8(profUser[5]), toUTF8(profUser[6]), toUTF8(profUser[7]), toUTF8(tentValQuestSection[quest][0]), toUTF8(tentValQuestSection[quest][1])

                    HistResps = ''

                    try:
                        print "Pesquisando o histórico: ", tentValQuestSection[quest][2], ' Usuario: ', usuario.userStudent
                        hsts = HistoricoQuestoes.objects.filter(campo=tentValQuestSection[quest][2], usuario=usuario.userStudent)
                        print "TAMANHO HIST: ", len(hsts)

                        for hst in hsts:
                            print "Hist: ", toUTF8(hst.valor)

                            HistResps += toUTF8(hst.valor) + ', '
                        print "Historico da Questao: ", HistResps

                    except:
                        print "Erro ao pegar hist"

                    writer.writerow(['A',
                            int(sec)+1,
                            int(quest)+1,
                            # questoesSection[quest][0],
                            toUTF8(questoesSection[quest][1]),
                            toUTF8(questoesSection[quest][2]),
                            toUTF8(profUser[0]),
                            toUTF8(profUser[1]),
                            toUTF8(profUser[2]),
                            toUTF8(profUser[3]),
                            toUTF8(profUser[4]),
                            toUTF8(profUser[5]),
                            toUTF8(profUser[6]),
                            toUTF8(profUser[7]),
                            toUTF8(tentValQuestSection[quest][0]),
                            toUTF8(tentValQuestSection[quest][1]),
                            HistResps ])

                    # print "year_of_birth ", profUser[7]

        # Arm B
        for UserID in range(0, TotalUsersB):
            userResps = ScoresPorQuestaoB[UserID]
            tentValQuest = exercInfoB[UserID][0]
            profUser = UserBProfile[UserID]

            print "Numero sections B: ", len(userResps)
            print "tentValQuest B: ", len(tentValQuest)
            print "userResps B: ", userResps
            print "tentValQuest B: ", tentValQuest


            # Faz a iteração pela quantidade de Sections
            for sec in range(0, len(userResps)):
                questoesSection = userResps[sec]
                tentValQuestSection = tentValQuest[sec]

                print
                # print "questoesSection: ", questoesSection
                print "Tamanho: B ", len(questoesSection)
                # print "tentValQuestSection: ", tentValQuestSection
                print


                # print "Section: ", sec, " questoes section: ", questoesSection, " tentValQuestSection: ", tentValQuestSection

                for quest in range(0, len(questoesSection)):

                    # print "Primeira"

                    # print 'B', int(sec)+1, int(quest)+1, questoesSection[quest][0]#,questoesSection[quest][1]#,
                    #         # questoesSection[quest][2],
                    #         # profUser[0],
                    #         # profUser[1],
                    #         # profUser[2],
                    #         # profUser[3],
                    #         # profUser[4],
                    #         # profUser[5],
                    #         # profUser[6],
                    #         # profUser[7],
                    #         # tentValQuestSection[quest][0],
                    #         # tentValQuestSection[quest][1]
                    HistResps = ''

                    try:
                        print "Pesquisando o histórico: ", tentValQuestSection[quest][2], ' Usuario: ', usuario.userStudent
                        hsts = HistoricoQuestoes.objects.filter(campo=tentValQuestSection[quest][2],usuario=usuario.userStudent)

                        print "TAMANHO HIST: ", len(hsts)

                        for hst in hsts:
                            print "Hist: ", toUTF8(hst.valor)

                            HistResps += toUTF8(hst.valor) + ', '

                        print "Historico da Questao: ", HistResps
                    except:
                        print "Erro ao pegar hist"

                    writer.writerow(['B',
                            int(sec)+1,
                            int(quest)+1,
                            # questoesSection[quest][0],
                            toUTF8(questoesSection[quest][1]),
                            toUTF8(questoesSection[quest][2]),
                            toUTF8(profUser[0]),
                            toUTF8(profUser[1]),
                            toUTF8(profUser[2]),
                            toUTF8(profUser[3]),
                            toUTF8(profUser[4]),
                            toUTF8(profUser[5]),
                            toUTF8(profUser[6]),
                            toUTF8(profUser[7]),
                            toUTF8(tentValQuestSection[quest][0]),
                            toUTF8(tentValQuestSection[quest][1]),
                            HistResps])


                # OK para a versao A, agora falta a versao B

            #
            # for secArm in range(0, len(tentValQuest)):
            #     # print "Section ", secArm, " Valor questoes ", userResps[secArm]
            #     questoesSection = userResps[secArm]
            #     tentValQuestSection = tentValQuest[secArm]
            #     print
            #     print " tentValQuestSection:  ", tentValQuestSection
            #     print " "
            #
            #     for quest in range(0, len(questoesSection)):
            #         print 'Section2', numSec , "Questão: ", quest, " Valor: ", questoesSection[quest], "Profile ", UserAProfile[UserID], "Tentatia e valor Digitado ", tentValQuestSection[quest]
            #         # writer.writerow([numSec , quest,  questoesSection[quest][0], questoesSection[quest][1],questoesSection[quest][2],   UserAProfile[UserID][0], UserAProfile[UserID][1], UserAProfile[UserID][2], UserAProfile[UserID][3], UserAProfile[UserID][4], UserAProfile[UserID][5], UserAProfile[UserID][6], UserAProfile[UserID][7],  tentValQuestSection[quest][0], tentValQuestSection[quest][1]])
            #     numSec -= 1





        # if TotalUsersA > 1:
        #     tanRange = len(ScoresPorquestaoA)/int(questoesA)
        #     print "Tan tanRange: ",  tanRange
        #
        #     for UserID in range(0, tanRange):
        #         for questUserID in range(0, int(questoesA)):
        #             writer.writerow(['A',
        #                              # TotalScoreA[UserID][0],
        #                              # TotalScoreApossibleA[UserID][0],
        #                              ScoresPorquestaoA[quant][0],
        #                              ScoresPorquestaoA[quant][1],
        #                              ScoresPorquestaoA[quant][2],
        #                              UserAProfile[UserID][0],
        #                              UserAProfile[UserID][1],
        #                              UserAProfile[UserID][2],
        #                              UserAProfile[UserID][3],
        #                              UserAProfile[UserID][4],
        #                              UserAProfile[UserID][5],
        #                              UserAProfile[UserID][6],
        #                              UserAProfile[UserID][7],
        #                              exercInfoA[questUserID][0][UserID][0],
        #                              exercInfoA[questUserID][0][UserID][1]])
        #             print 'A',ScoresPorquestaoA[quant][0],ScoresPorquestaoA[quant][1], exercInfoA[questUserID][0][UserID][0], exercInfoA[questUserID][0][UserID][1]
        #
        #             print "questUserID: ", questUserID, " exercInfoA[UserID][0] ",  exercInfoA[UserID][0], "Score: ", UserID
        #             print
        #
        #
        #             quant+=1
        # print "ASLDFLJASJDFLASLDFJLJASDLFJLKSJDF"
        # if TotalUsersB > 1:
        #     quant = 0
        #     for UserID in range(0, len(ScoresPorQuestaoB)/int(questoesB)):
        #         for questUserID in range(0, int(questoesB)):
        #             # print "Quant ", quant, "Val: ", UserBProfile[quant][0] if UserBProfile[quant][0]!=u'' else 'jj'
        #             writer.writerow(['B',
        #                              # TotalScoreB[questUserID][0],
        #                              # TotalScorePossibleB[questUserID][0],
        #                              ScoresPorQuestaoB[quant][0],
        #                              ScoresPorQuestaoB[quant][1],
        #                              ScoresPorQuestaoB[quant][2],
        #                              UserBProfile[UserID][0],
        #                              UserBProfile[UserID][1],
        #                              UserBProfile[UserID][2],
        #                              UserBProfile[UserID][3],
        #                              UserBProfile[UserID][4],
        #                              UserBProfile[UserID][5],
        #                              UserBProfile[UserID][6],
        #                              UserBProfile[UserID][7],
        #                              exercInfoB[questUserID][0][UserID][0],
        #                              exercInfoB[questUserID][0][UserID][1]] )
        #             quant+=1

        return response # CSV file


    except:
        print "Houve um erro ao retornar a lista"
        e = sys.exc_info()

        # print "Error: %s " % e

        return HttpResponse("<h1>Houve um erro ao pesquisar no Banco de Dados! </h1>")



def toUTF8(val):

    # print "Type: ", type(val)

    try:
        if type(val) == type(5) or type(val) == type(44444444444444444444):
            # print "int", val
            return val

        if type(val) == type(5.5):
            # print "float", val
            return val

        if isinstance(val, unicode):
            # print "unicode", val
            return val.encode('utf8')

        if type(val) == type(None):
            # print "None", val
            return ""

        if type(val) == type([]): # List
            cont=0
            STR ='('
            for i in val:
                cont+=1
                if cont==len(val):
                    STR+=i+')'
                else:
                    STR+=i+', '
            return STR


        # print "Outro: ", type(val), val
        return unicode(val, 'utf-8')+""

    except:
        print
        print "Erro"
        print "Val: ", val
        print "Type: ", type(val)

        return ""



def fetch_reverify_banner_info(request, course_id):
    """
    Fetches needed context variable to display reverification banner in courseware
    """
    reverifications = defaultdict(list)
    user = request.user
    if not user.id:
        return reverifications
    enrollment = CourseEnrollment.get_or_create_enrollment(request.user, course_id)
    course = course_from_id(course_id)
    info = single_course_reverification_info(user, course, enrollment)
    if info:
        reverifications[info.status].append(info)
    return reverifications

