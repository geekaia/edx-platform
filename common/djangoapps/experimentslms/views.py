# -*- coding: utf-8 -*-

# from collections import defaultdict
from django.http import HttpResponse
import csv
import sys

from experiments.models import *
# from student.models import CourseEnrollment
# from student.views import course_from_id, single_course_reverification_info
from utils import progress
from student.models import UserProfile
from django.contrib.auth.decorators import login_required

def toUTF8(val):
    """ Converte algumas variaveis para UTF-8 """

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

        return ""


@login_required
def DesignAsCSV(request, course_id,  idExp):
    """
    Nesta opçao, mostra as questoes em colunas no arquivo CSV. Caso seja utilizado um Design do experimento personalizado, então será considerado a ordem do Design.
    Isto facilita na hora de importar para softwares como Minitab, Jmp e R.

    Argumentos:
      request: http request default
      course_id:  variavel
      idExp: id do experimento

    No arquivo CSV contera:
      'user'
      'location'
      'city'
      'country'
      'gender'
      'language'
      'level_of_education'
      'year_of_birth'
      'Quest 0'
      'Quest 1'
       ...
    """

    # Lista dos arms
    try:
        # Pega os experimento
        exp = ExperimentDefinition.objects.get(id=int(idExp))

        # Pega todos os usuarios do experimento
        versionUsers = UserChoiceExperiment.objects.filter(experimento=exp)

        rows = []
        MaxQuestoes = 0

        for ChoiceUser in versionUsers:

            courseware_summary = []

            row={}

            # Tem que pegar o Score de um módulo específico
            try:
                courseware_summary = progress(request, course_id, ChoiceUser.userStudent.id)

            except:
                courseware_summary = []

            # Get information about the user
            try:
                userprofile = UserProfile.objects.get(user=ChoiceUser.userStudent)

                # Esta ordem vai de acordo com o que foi expecificado na primeira linha do CSV
                row['user'] = toUTF8(userprofile.user.__unicode__())
                row['location'] = toUTF8(userprofile.location)
                row['city'] = toUTF8(userprofile.city)
                row['country'] = toUTF8(userprofile.country.__unicode__())
                row['gender'] = toUTF8(userprofile.gender)
                row['language'] = toUTF8(userprofile.language)
                row['level_of_education'] = toUTF8(userprofile.level_of_education)
                row['bloco'] = ChoiceUser.bloco

                # Versions of Arms
                versions = {'A': 0, 'B': 1, 'C': 2, 'D' : 3}
                row['arm'] = versions[ChoiceUser.versionExp.version]
            except:
                print "Exceção ao pegar o profile do ChoiceUser"

            # Pega o resultado de cada questao
            exercicios = []
            for chapter in courseware_summary:
                if ChoiceUser.versionExp.sectionExp_url == chapter['url_name']:
                    for section in chapter['sections']:
                        if len(section['scores']) > 0:
                            for UserID in section['scores']:
                                # Get the score Earned
                                exercicios.append(UserID.earned)

            if len(exercicios) > MaxQuestoes:
                MaxQuestoes = len(exercicios)

            # Todos os exercicios de uma section
            row['exercicios'] = exercicios


            rows.append(row)

        # Gera um arquivo CSV a partir dos dados coletados do aluno
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="RelatorioDesign.csv"'

        writer = csv.writer(response)

        quant = 0

        # Generate the first Line of CSV file
        listCols = []
        listCols.append('user')
        listCols.append('location')
        listCols.append('city')
        listCols.append('country')
        listCols.append('gender')
        listCols.append('language')
        listCols.append('level_of_education')
        listCols.append('block')
        listCols.append('ARM')

        # Questoes -- A quantidade sera o somatorio de todas as questoes das sections
        # Aqui so mostrara o score obtido nas questoes

        # Exercicio Labels collunns
        for exercNumc in range(0, MaxQuestoes):
            listCols.append('Quest '+str(exercNumc))

        writer.writerow(listCols)

        for row in rows:
            # Csv line
            line = []

            line.append(row['user'])
            line.append(row['location'])
            line.append(row['city'])
            line.append(row['country'])
            line.append(row['gender'])
            line.append(row['language'])
            line.append(row['level_of_education'])
            line.append(row['bloco'])
            line.append(row['arm'])


            # Para dar certo é necessário que em todos arms do experimento tenham a mesma quantidade de exercícios.
            # Caso não haja a mesma quantidade será necessário
            maxExercAtual = len(row['exercicios'])

            # Caso haja um módulo com mais exercícios será possível será adicoonado linhas em branco
            for i in range(0, MaxQuestoes):
                if i < maxExercAtual:
                    line.append(row['exercicios'][i])
                else:
                    line.append("")

            writer.writerow(line)

        # CSV file
        return response


    except Exception, e:
        print "Houve um erro ao retornar a lista"


        print "Error: %s " % e

        return HttpResponse("<h1>Houve um erro ao pesquisar no Banco de Dados! </h1>")


@login_required
def expAnalise(request, course_id,  idExp):
    """ Esta funçao  permite que gerar um arquivo CSV com todas as informaçoes do Experimento.

        Argumentos:
          request: http request default
          course_id:  variavel

        No arquivo CSV contera:
          'arm' -- A ou B
         'section' -- EdX section
         'Questao' -- Numero da seçao
         'Bloco', -- bloco, caso seja utilizado alguma randomizaçao por blocos
         'ScoreObtido' -- Score conceito pelo aluno ao
         'MaxScore' -- Score maximo possivel para esta questao
         'usuario' -- usuario do que fez o Arm

         Dados do profile do usuario
         'location'
         'city'
         'country',
         'gender',
         'language',
         'level_of_education',
         'year_of_birth',

         'tentativas' -- quantidade de tentativas criadas
         'Resposta'  - resposta da questao -- TODO
         'Historico Resps' - Historico de cada Questao -- TODO

        Tais informaçoes podem ser utilizadas para realizaçao de uma analise com alguns softwares, tais como: Excell, LibreOffice e outros.
    """

    # Ideias

    # Pegar o UserID de todos os usuarios que participaram do experimento User Choice
    # Somar o UserID para as opções A e B
    # Calcular os gráficos de Barras com Intervalo de Confiança
    # Plotar T-test e outros Testes
    # Verificar se o usuario

    # Pega o Grading de acordo com o UserID do usuario
    # Pega o Grading de acordo com o UserID do usuario
    # primeiro tenho que pegar os registros deste experimento


    try:
        # Pega os experimento
        exp = ExperimentDefinition.objects.get(id=int(idExp))

        # Pega todos os usuarios do experimento
        usuariosParticipantes = UserChoiceExperiment.objects.filter(experimento=exp)


        TotalUsersA = 0 # OK -- Funciona
        ScoresPorquestaoA=[]  # OK -- ja funciona
        UserAProfile=[] # OK -- ja funciona
        exercInfoA=[] # Tem que envelopar igual ao PorquestaoA

        TotalUsersB = 0
        ScoresPorQuestaoB=[]
        UserBProfile=[]
        exercInfoB=[]

        TotalUsersC = 0
        ScoresPorQuestaoC=[]
        UserCProfile=[]
        exercInfoC=[]



        for usuario in usuariosParticipantes:

            courseware_summary = []

            # Tem que pegar o Score de um módulo específico
            try:
                courseware_summary = progress(request, course_id, usuario.userStudent.id)

            except:
                courseware_summary = []


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
                usrprofl.append(usuario.bloco)

            except:
                print "Exceção ao pegar o profile do usuario"

            for chapter in courseware_summary:

                if usuario.versionExp.sectionExp_url == chapter['url_name']:
                    earned = []
                    total = []

                    exercInfo=[]
                    #
                    # TotalScoreAUser = [] # Quantidade de acertos de A Necessita envelopar User e Subsection
                    # TotalScoreApossibleAUser = [] # Quant. total de questoes getScore pega isso
                    # TotalUsersAUser = 0
                    ScoresPorquestaoAUser=[]
                    ScoresPorquestaoBUser=[]
                    ScoresPorquestaoCUser=[]

                    # exercInfoAUser=[]

                    # UserAProfileUser=[]
                    exercInfoAUser=[]
                    exercInfoBUser=[]
                    exercInfoCUser=[]


                    if usuario.versionExp.version == 'A':
                        TotalUsersA = TotalUsersA + 1
                    elif usuario.versionExp.version == 'B':
                        TotalUsersB = TotalUsersB + 1
                    else:
                        TotalUsersC = TotalUsersC + 1


                    for section in chapter['sections']:
                        earned.append(section['section_total'].earned)
                        total.append(section['section_total'].possible)
                        # info = section['inforExerc'].reverse()
                        # info.reverse()
                        exercInfo.append(section['inforExerc'])


                        if usuario.versionExp.version == 'A':

                            exercInfoAUser.append(exercInfo)

                            if len(section['scores']) > 0:
                                # Falta os Scores de cada exercício
                                exercicio = 1
                                sectionExec = []

                                for UserID in section['scores']:
                                    SCORE = []
                                    SCORE.append(exercicio) # numero do exercicio
                                    SCORE.append(UserID.earned) # o Quanto conseguiu
                                    SCORE.append(UserID.possible) # Maximo possivel
                                    exercicio+=1
                                    sectionExec.append(SCORE)


                                ScoresPorquestaoAUser.append(sectionExec)


                        elif usuario.versionExp.version == 'B':
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

                        else:
                            # TotalScoreB.append(earned)
                            # TotalScorePossibleB.append(total)
                            exercInfoCUser.append(exercInfo)

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

                                ScoresPorquestaoCUser.append(sectionExec)


                    if usuario.versionExp.version == 'A':
                        # print "Score User: ", ScoresPorquestaoAUser
                        ScoresPorquestaoA.append(ScoresPorquestaoAUser)
                        UserAProfile.append(usrprofl)
                        exercInfoA.append(exercInfoAUser)
                        # TotalScoreA.append(TotalScoreAUser)
                    elif usuario.versionExp.version == 'B':
                        ScoresPorQuestaoB.append(ScoresPorquestaoBUser)
                        UserBProfile.append(usrprofl)
                        exercInfoB.append(exercInfoBUser)
                    else:
                        ScoresPorQuestaoC.append(ScoresPorquestaoCUser)
                        UserCProfile.append(usrprofl)
                        exercInfoC.append(exercInfoCUser)



        quant=0


        try:
            questoesA = len(ScoresPorquestaoA)/TotalUsersA
        except:
            questoesA = 0



        try:
            questoesB = len(ScoresPorQuestaoB)/TotalUsersB
        except:

            questoesB = 0

        try:
            questoesC = len(ScoresPorQuestaoC)/TotalUsersC
        except:

            questoesC = 0


        # Gera um arquivo CSV a partir dos dados coletados do aluno
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio2.csv"'

        writer = csv.writer(response)

        quant = 0
        writer.writerow(['arm',
                         'section',
                         'Questao',
                         'Bloco',
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



            lop=0
            # Faz a iteração pela quantidade de Sections
            for sec in range(0, len(userResps)):

                questoesSection = userResps[sec]
                tentValQuestSection = tentValQuest[sec]

                for quest in range(0, len(questoesSection)):
                    print 'A', int(sec)+1,  int(quest)+1,  toUTF8(questoesSection[quest][0]), toUTF8(questoesSection[quest][1]), toUTF8(questoesSection[quest][2]), toUTF8(profUser[0]), toUTF8(profUser[1]), toUTF8(profUser[2]), toUTF8(profUser[3]), toUTF8(profUser[4]), toUTF8(profUser[5]), toUTF8(profUser[6]), toUTF8(profUser[7]), toUTF8(tentValQuestSection[quest][0]), toUTF8(tentValQuestSection[quest][1])

                    HistResps = ''

                    try:
                        hsts = HistoricoQuestoes.objects.filter(campo=tentValQuestSection[quest][2], usuario=usuario.userStudent)

                        for hst in hsts:

                            HistResps += toUTF8(hst.valor) + ', '

                    except:
                        print "Erro ao pegar hist"

                    writer.writerow(['A',
                            int(sec)+1,
                            int(quest)+1,
                            toUTF8(profUser[8]),
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


            # Faz a iteração pela quantidade de Sections
            for sec in range(0, len(userResps)):
                questoesSection = userResps[sec]
                tentValQuestSection = tentValQuest[sec]

                for quest in range(0, len(questoesSection)):


                    HistResps = ''

                    try:
                        hsts = HistoricoQuestoes.objects.filter(campo=tentValQuestSection[quest][2],usuario=usuario.userStudent)

                        for hst in hsts:
                            print "Hist: ", toUTF8(hst.valor)

                            HistResps += toUTF8(hst.valor) + ', '

                    except:
                        print "Erro ao pegar hist"

                    writer.writerow(['B',
                            int(sec)+1,
                            int(quest)+1,
                            toUTF8(profUser[8]),
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

        # Arm C
        for UserID in range(0, TotalUsersC):
            userResps = ScoresPorQuestaoC[UserID]
            tentValQuest = exercInfoC[UserID][0]
            profUser = UserCProfile[UserID]


            # Faz a iteração pela quantidade de Sections
            for sec in range(0, len(userResps)):
                questoesSection = userResps[sec]
                tentValQuestSection = tentValQuest[sec]

                for quest in range(0, len(questoesSection)):


                    HistResps = ''

                    try:
                        hsts = HistoricoQuestoes.objects.filter(campo=tentValQuestSection[quest][2],usuario=usuario.userStudent)

                        for hst in hsts:
                            print "Hist: ", toUTF8(hst.valor)

                            HistResps += toUTF8(hst.valor) + ', '

                    except:
                        print "Erro ao pegar hist"

                    writer.writerow(['B',
                            int(sec)+1,
                            int(quest)+1,
                            toUTF8(profUser[8]),
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



        return response # CSV file


    except:
        print "Houve um erro ao retornar a lista"
        e = sys.exc_info()

        # print "Error: %s " % e

        return HttpResponse("<h1>Houve um erro ao pesquisar no Banco de Dados! </h1>")




