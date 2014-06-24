#coding: utf-8
#from social.backends import username

__author__ = 'geekaia'


#from random import *
from experiments.models import *
import sys
# Experimento uniforme
from planout.experiment import SimpleExperiment
from planout.ops.random import *
from django.contrib.auth.models import User

# def getQuantExp(Exp, 'A'):
#
#
#     try:
#         print "asdfasdfasdf"
#     except:
#         return 0



def cadastraVersao(user,URL,urlExp ):
    try:
        # Producura os para o experimento urlEXP.experimento
        opcs = OpcoesExperiment.objects.filter(experimento=urlExp.experimento)

        options = {} # Pega todas as versões disponíveis A e B
        CHOICES=[]# Opções do experimento. Este é o parâmetro do PlanOut
        lenV={} # Tamanh das versões

        max=0
        curso = None

        for opc in opcs:
            options[opc.version] = opc
            CHOICES.append(opc.sectionExp_url)
            curso = opc.experimento.course

            quant = UserChoiceExperiment.objects.filter(versionExp=opc)

            lenV[opc.version] = len(quant)

            if lenV[opc.version] >= max:
                max = lenV[opc.version]

        print "CHOICES: ", CHOICES

        # Escolhe uma para o usuario
        print "User.id: ", user.id

        CHOICESG = CHOICES

        class UrlExperiment(SimpleExperiment):
          def assign(self, params, userid):
            params.URL = UniformChoice(choices=CHOICESG,
              unit=userid)

        exp = UrlExperiment(userid=user.id)

        URLChoice=""

        try:

            URLChoice = exp.get('URL')
        except:
            print "Unexpected error:", sys.exc_info()[0]


        print "URLChoice: ", URLChoice

        # num = randint(1,2)
        num = CHOICES.index(URLChoice)

        versao = None

        if num == 0:
            versao = 'A' # Removi o balanceamento de 50 50
            # if max != lenV['A']:
            #     versao = 'A'
            # else:
            #     versao = 'B'

        else:
            versao = 'B'
            # if max != lenV['B']:
            #     versao = 'B'
            # else:
            #     versao = 'A'


        # Um usuário que escolhe uma versão
        # estará nela para sempre
        # e todo o sempre

        if curso:
            expsCurso = ExperimentDefinition.objects.filter(course=curso)

            print "tamanho: ", len(expsCurso)

            for experi in expsCurso:
                userChoice = UserChoiceExperiment.objects.filter(userStudent=user, experimento=experi)

                if len(userChoice)>0:
                    for usrC in userChoice:
                        versao = usrC.versionExp.version
                        print "EU JA ESCOLHI UMA VERSAO QUE E: ", usrC.versionExp.version


        # Grava a versão escolhida
        userVersion = UserChoiceExperiment()
        userVersion.userStudent = user
        userVersion.versionExp = options[versao]
        userVersion.experimento = urlExp.experimento
        userVersion.save()

        # print Versão escolhida
        print "Versão escolhida: ", userVersion.versionExp.sectionExp_url
        print "Versao Letra: ", versao
        print "Versão UR escolhidaL ", options[versao].sectionExp_url
        print "Versão A ",  options['A'].sectionExp_url
        print "Versão B ",  options['B'].sectionExp_url
        print "URL: ", URL

        if userVersion.versionExp.sectionExp_url == URL:
            print "Quarto"

            return True
        else:
            print "Quinto"
            return False
    except:
        print "Sexto"
        return False


def VerABprint(URL, user):
    try:

        # Verifica se usuário é Staff, caso seja ele não poderá participar
        # do Experimento
        try:
            usr = User.objects.get(pk=user.id)

            if usr.is_staff:
                print "É staff"
                return True
        except:
            print "Erro pegar o usuario"


        # Procura na base de dados para ver se a URL informada faz parte de um Experimento
        print "URL testada", URL, "Usuario: ", user
        urlExp = OpcoesExperiment.objects.get(sectionExp_url=URL)

        # Se faz parte, procura-se na base de dados pela URL
        # Verifica se esta URL foi escolhida pelo usuario
        try:
            # Se o experimento desta URL já foi escolhida pelo aluno como
            expsChoices = UserChoiceExperiment.objects.filter(experimento=urlExp.experimento, userStudent=user)

            # Só será considerado TRUE se for igual a URL
            print "Tamanho da dos Registros: ",  len(expsChoices)
            print "Tamanho da dos Registros: ",  len(expsChoices)


            if len(expsChoices) == 1: # 1 pq o usuário só pode escolher 1 versão do experimento
                # Verifica-se se a opção do experimento é a atual
                # sempre pega o primeiro registro, pois só pode ter 1
                if expsChoices[0].versionExp.sectionExp_url == URL: # A variável do Experimento tb deve ser igual
                    print "Primeiro"
                    return True
                else:
                    print "Segundo"
                    return False
            else:
                if len(expsChoices) == 0:
                    return cadastraVersao(user,URL,urlExp)
                else:
                    print "Terceiro"
                    return False

        except:
            # Neste ponto o usuário não o selecionou uma opção, então deve-se
            # Atribuir a este usuário uma versão

            return cadastraVersao(user,URL,urlExp)


    except:
        print "Caso a URL não pertença a nenhum experimento"

        return True



def pulaURL(URL, user):
    try:
        # Procura na base de dados para ver se a URL informada faz parte de um Experimento
        print "URL testada", URL, "Usuario: ", user
        urlExp = OpcoesExperiment.objects.get(sectionExp_url=URL)

        # Se faz parte, procura-se na base de dados pela URL
        # Verifica se esta URL foi escolhida pelo usuario
        try:
            # Se o experimento desta URL já foi escolhida pelo aluno como
            expsChoices = UserChoiceExperiment.objects.filter(experimento=urlExp.experimento, userStudent=user)

            # Só será considerado TRUE se for igual a URL
            print "Tamanho da dos Registros: ",  len(expsChoices)

            if len(expsChoices) == 1: # 1 pq o usuário só pode escolher 1 versão do experimento
                # Verifica-se se a opção do experimento é a atual
                # sempre pega o primeiro registro, pois só pode ter 1
                if expsChoices[0].versionExp.sectionExp_url == URL: # A variável do Experimento tb deve ser igual
                    print "Primeiro"
                    return False
                else:
                    print "ESTA URL NAO FOI SELECIONADA PELO USUARIO"
                    return True

        except:

            return False

    except:
        print "Caso a URL não pertença a nenhum experimento não precisa PULAR"

        return False

def urlsExcluir(user):

    listURLandExps=[]

    # Pega todos os experimentos que o usuario participou
    expUser = UserChoiceExperiment.objects.filter(userStudent=user)

    # len > 1
    if len(expUser) > 0:
        # Agora tem que pegar as URLs associadas ao usuario

        for exPart in expUser:

            # Pega todas as urlS dos experimentos que o usuario participou
            listURLSeXPS = OpcoesExperiment.objects.filter(experimento=exPart.experimento)

            if len(listURLSeXPS)>0:
                for urlsEXP in listURLSeXPS:
                    # Adiciona todos exceto as que o usuario escolheu
                    if exPart.versionExp.sectionExp_url != urlsEXP.sectionExp_url:
                        listURLandExps.append(urlsEXP.sectionExp_url)


        return listURLandExps

    else:
        return listURLandExps




# Pega todos os experimentos