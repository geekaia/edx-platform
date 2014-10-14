#coding: utf-8
#from social.backends import username

__author__ = 'geekaia'


#from random import *
from experiments.models import *
import sys
# Experimento uniforme
from django.contrib.auth.models import User
from planout.experiment import SimpleExperiment
from planout.ops.random import *
from planout.interpreter import *
import json
import hashlib
from abc import ABCMeta, abstractmethod

from student.models import UserProfile
from datetime import date



import threading
from threading import Thread

# Global tread, que servirá para quando tivermos requisições concorrentes
lock = threading.Lock()


class CadVersao(Thread):
    """
        This thread allows for entries to the table UserChoiceExperiment only be written one at a time. This is necessary since 
        there has to be a pre-established order, ensuring that the order be respected, also guaranteeing that there will not be
        any two entries for a single experiment

        Este thread propicia que as entradas na tabela UserChoiceExperiment só serão cadastradas um por vez, pois é necessário ter uma ordem
        pré-estabelecida e isto assegura que a ordem será respeitada, assim como garante que não serão inseridos 2 registros
        de um experimento.
    """

    def __init__(self, chapter, usuario):
        Thread.__init__(self)
        self.chapter=chapter
        self.usuario=usuario

    def run(self):
        chapter=self.chapter
        usuario=self.usuario
        lock.acquire() #acquire the lock
        self.vercad = VerABprint(chapter, usuario)
        lock.release()

    def getResult(self):
        return self.vercad


# IDEIA -- criar uma função que permita comparar verificar a quantidade de registros com o nome do usuário deste experimento
def NeedThread(user, course):
    """
    Verify whether it is necessary to have a thread to register a user

    Step 1: take all experiment from a course
    Step 2: compare with userChoice, and if it has an equal number of experiments then a thread is not necessary
    Step 3: return True if the number from userchoice is different from the number of experiments, and if it is equatl
    then return False

    :param course: current course
    :return: false if there is no need for a Thread and True if it is NeedThread





    Verifica se será necessário um thread para cadastrar o usuário.

    Passo 1 - pega todos os experimentos de um curso
    Passo 2 - Compara com o userChoice, caso seja igual ao de experimentos não é necessário um thread
    Passo 3 - retorna True se o número do userchoice for diferente da quantidade de experimentos, caso seja igual retorna False

    :param course: curso atual
    :return: false caso não precise de um Thread e True caso precise
    """

    # Pega a quantidade de experimentos de um curso
    listExps = ExperimentDefinition.objects.filter(course=course.location)
    # Pega a quantidade de registros da tabela
    tamanho = 0

    for exp in listExps:
        listOpcs = UserChoiceExperiment.objects.filter(experimento=exp, userStudent=user)
        tamanho += len(listOpcs)

    if len(listExps) == tamanho:
        return False
    else:
        return True


def cadastraVersao(user,URL,urlExp):
    """
    This function creates a randomization and right after creates a registry for the entity UserChoiceExperiment. Randomization happen in an 
    agreement between whatever might be expressed in the StrategyRandomization entity in the strategyType field. Currently, it is possible
    to alternate between the two randomization schemes: UniformChoice, WeightedChoice, PlanoutScript and CustomDesign (experiment design
        done through R, JMP, SAS or Minitab)

    :param user: student
    :param URL: url that the use is attempting to access
    :param urlExp:
    :return: file in CSV format






    Esta função faz a randomização e em seguida faz o cadastro na entidade UserChoiceExperiment. A randomização ocorre de acordo com o que estiver
    definido na entidade StrategyRandomization no campo strategyType. Atualmente é possível alternar entre as randomizações:
            UniformChoice, WeightedChoice, PlanoutScript e CustomDesign (design do experimento criado pelo R, JMP, SAS ou Minitab)

    :param user: aluno
    :param URL: url que o usuário está tentando acessar
    :param urlExp:
    :return: file in CSV format
    """

    try:
        # Producura os para o experimento urlEXP.experimento
        opcs = OpcoesExperiment.objects.filter(experimento=urlExp.experimento)

        options = {} # Pega todas as versões disponíveis A e B
        CHOICES=[]# Opções do experimento. Este é o parâmetro do PlanOut
        lenV={} # Tamanh das versões

        URLChoice = ""

        curso = None
        strat=''
        ExpPart = None
        versao = None
        conversao = False
        deuerro = False

        for opc in opcs:
            options[opc.version] = opc
            CHOICES.append(opc.sectionExp_url)
            curso = opc.experimento.course
            quant = UserChoiceExperiment.objects.filter(versionExp=opc)
            lenV[opc.version] = len(quant)
            ExpPart = opc.experimento
            strat = opc.experimento.strategy # Pega a estratégia de randomização

        CHOICESG = CHOICES
        exp = None
        bloco = 0

        # Pega a estratégia de randomização
        if strat.strategyType == 'UniformChoice':
            class UrlExperiment(SimpleExperiment):
              def assign(self, params, userid):
                params.URL = UniformChoice(choices=CHOICESG, unit=userid)

            exp = UrlExperiment(userid=user.id)

        elif strat.strategyType == 'crossover':

            # Steps: 1 - pega todas as versões
            letras = ['A', 'B', 'C', 'D', 'E']

            dicts = {}
            cont = 0
            for i in CHOICESG:
                dicts[letras[cont]] = options[letras[cont]].sectionExp_url
                cont += 1

            print "Dicts: ", dicts

            OpcsSel = {}
            # Procura por todas as versões anteriormente selecionadas que sejam do tipo CrossOver
            #opcs = OpcoesExperiment.objects.filter(experimento=urlExp.experimento)
            expsCourse = ExperimentDefinition.objects.filter(course=urlExp.experimento.course)

            # Verifica as versões escolhidas em cada experimento
            chs = []
            quantNecess = 0

            # Pega todos os experimentos crossover
            for expc in expsCourse:
                if expc.strategy.strategyType == "crossover" and expc.strategy.periodoRel == urlExp.experimento.strategy.periodoRel:
                    if expc.strategy.periodoRel == expc: # É o mesmo que o atual, ou seja o primeiro crossover
                        quantNecess = int(expc.strategy.periodos)

                        try:
                            choic = UserChoiceExperiment.objects.get(experimento=expc, userStudent=user)
                            chs.append(choic.versionExp)
                        except:
                            print 'code 1 crossover'
                    else:
                        try:
                            choic = UserChoiceExperiment.objects.get(experimento=expc, userStudent=user)
                            chs.append(choic.versionExp)
                        except:
                            print 'code 2 crossover'

            # Apaga todas as versoes ja foram usadas
            print "Antes: "
            print "Chs: ", chs
            print "dicts: ", dicts

            for ch in chs:
                if ch.version in dicts:
                    print "Tenho que remover ", ch.version
                    del dicts[ch.version]

            print "Depois"
            print "Chs: ", chs
            print "dicts: ", dicts

            if len(dicts) == 0:
                print 'Tudo ja foi selecionado!!!'

            CHS =[]
            for dic in dicts:
                CHS.append( dicts[dic] )

            print "Quant que será randomizada: ", CHS

            # As opcoes ja selecionadas serao desconsideradas
            class UrlExperiment(SimpleExperiment):
                def assign(self, params, userid):
                    params.URL = UniformChoice(choices=CHS, unit=userid)

            exp = UrlExperiment(userid=user.id)

            try:
                urlchoice = exp.get('URL')

                for i in dicts:
                    if dicts[i] == urlchoice:
                        versao = i

                conversao = True
            except:
                print 'erro'

            print "UrlChoice: ", urlchoice
            print "Versao: ", versao

        elif strat.strategyType == 'cluster':
            # Step 1 - randomiza os clusters entre os Arms disponíveis
            groups = GroupsCluster.objects.filter(experiment=ExpPart)

            listToRandomize=[]

            # Verifica em que grupo o usuario pertence
            # Pega todos os dados do usuario
            profUser = UserProfile.objects.get(user=user)
            age = date.today().year - profUser.year_of_birth
            city = profUser.city
            pais = profUser.country.code
            escolaridade = profUser.level_of_education
            sexo = profUser.gender

            #############################################
            #  Step 1 -  Procura pelo grupo do Usuario
            #############################################
            groupUser = -1 # isto quer dizer que o usuario nao tem nenhum trupo
            for group in groups:
                # Verifica criterio por criterio
                matchCrits = False

                # Todos os grupos que nao foram randomizados
                if group.versao is None:
                    listToRandomize.append(group.id)

                try:
                    Group = json.loads(group.grupos)
                except:
                    print "Other Group"
                    continue

                print "Group: ", Group

                for criterio in Group:
                    print "Criterio: ", criterio

                    if criterio['tipo'] == 'sexo':
                        if eval("sexo=='"+criterio['val']+"'"):
                            print "match sexo ", criterio['val']
                            matchCrits = True
                            continue
                    elif criterio['tipo'] == 'escolaridade':
                        print "escolaridade == '"+criterio['val']+"'"
                        if eval("escolaridade == '"+criterio['val']+"'"):
                            print "match escolaridade", criterio['val']
                            matchCrits = True
                            continue
                    elif criterio['tipo'] == 'pais':
                        if eval("pais == '"+criterio['val']+"'"):
                            print "match pais", criterio['val']
                            matchCrits = True
                            continue
                    elif criterio['tipo'] == 'age':
                        if eval("age " + criterio['c_age'] + criterio['val']):
                            print "match age", criterio['val'], " age: ", age
                            matchCrits = True
                            continue
                    elif criterio['tipo'] == 'city':
                        print "match city", criterio['val']
                        from unicodedata import normalize
                        # Isto requer que o usuario se cadastre corretamente. Por exemplo, se for digitado SÕA PAULO ao invés de são paulo não
                        # entrara no grupo
                        cityUser = normalize('NFKD', city).encode('ASCII','ignore').lower()
                        cityCad = normalize('NFKD', criterio['val']).encode('ASCII','ignore').lower()

                        if cityCad in cityUser:
                            matchCrits = True
                            continue

                    matchCrits = False
                    break

                print "MatchCrits para entrar no grupo: ", criterio, ' group ', group.id, " matchCrits ", matchCrits
                # O usuario sera cadastrado no primeiro que preencher todos os requisitos
                if matchCrits == True:
                    groupUser = group.id
                    break

                print "Groupuser: ", groupUser


            # Pesquisa para ver se o grupo do aluno já teve randomização
            if groupUser != -1:
                groupMatch = GroupsCluster.objects.get(pk=groupUser)

                print 'g match searchi', groupMatch.versao != None, "Val"

                if groupMatch.versao != None:
                    print 'G  match is none'
                    versao = groupMatch.versao.version
                    achei = True
                    conversao = True
                    deuerro = False
                    URLChoice = options[versao].sectionExp_url
                else:
                    print "CadastraGrupo -- cadastra normal com randomização dos grupos "
                    versao, achei, conversao, deuerro = cadGrupo(groupUser, groups, ExpPart, user.id)
                    URLChoice = options[versao].sectionExp_url

                    print "Versão: ", versao, "Url choice: ", URLChoice, " CONVERSAO: ", conversao, " Deurro: ", deuerro
                    # Versão:  A Url choice:  427007a51f9c475ca12861aa898f2894  CONVERSAO:  True  Deurro:  False

            else:
                # Cadastra Other - quer dizer que o aluno nao entrou em nenhum grupo
                versao, achei, conversao, deuerro = cadGrupo(groupUser, groups, ExpPart, user.id)
                URLChoice = options[versao].sectionExp_url
                print "Versão: ", versao, "Url choice: ", URLChoice, " CONVERSAO: ", conversao, " Deurro: ", deuerro

        elif strat.strategyType == 'WeightedChoice':
            percents = []

            per = strat.percents.split(';')
            for i in per:
                percents.append(float(i))

            class UrlExperimentWeighted(SimpleExperiment):
              def assign(self, params, userid):
                params.URL = WeightedChoice(choices=CHOICESG, weights=percents, unit=userid)

            # ct = float(strat.percent1)
            exp = UrlExperimentWeighted(userid=user.id)
        elif strat.strategyType == 'customdesign':
            try:
                # Script:
                # Pega a quantidade de versões para este design deste experimento
                # Confronta com a do Design

                linhas = strat.customDesign.splitlines()
                tamL = len(linhas)

                # usuarios versão experimento
                choicesSelUsr = UserChoiceExperiment.objects.filter(experimento=ExpPart)
                lenC = len(choicesSelUsr)+1

                linRand = linhas[lenC]
                verL = linRand.split(',')[0]
                # convert to int
                ver = int(verL)
                if ver == 0:
                    versao ='A'
                elif ver == 1:
                    versao = 'B'
                else:
                    versao = 'C'

                URLChoice = CHOICESG[ver]

                achei = True
                conversao = True
                deuerro = False

            except:
                print "Deu Merda na leitura do campo"
                deuerro = True

        elif strat.strategyType == 'fatorial':
            try:
                # Script:
                # Pega a quantidade de versões para este design deste experimento
                # Confronta com a do Design

                linhas = strat.customDesign.splitlines()
                tamL = len(linhas)

                # usuarios versão experimento
                choicesSelUsr = UserChoiceExperiment.objects.filter(experimento=ExpPart)
                lenC = len(choicesSelUsr)+1

                linRand = linhas[lenC]

                fat1 = int(linRand.split(';')[4]) # 7;1;1;1;2;1
                fat2 = int(linRand.split(';')[5]) # 7;1;1;1;2;1

                """
                Combinação	Fator1	Fator2
                0           1     	  1
                1	        2         2
                2	        1         2
                3           2         1
                """

                if fat1==1 and fat2==1:
                    ver=0
                elif fat1==2 and fat2==2:
                    ver=1
                elif fat1==1 and fat2==2:
                    ver=2
                elif fat1==2 and fat2==1:
                    ver=3

                # Internamente ainda funciona com versoes A, B, C e D
                if ver == 0:
                    versao ='A'
                elif ver == 1:
                    versao = 'B'
                elif ver == 2:
                    versao = 'C'
                else:
                    versao = 'D'

                URLChoice = CHOICESG[ver]

                achei = True
                conversao = True
                deuerro = False

            except:
                print "Deu Merda na leitura do campo"
                deuerro = True

        elif strat.strategyType == 'planOut':
            try:
                class SimpleInterpretedExperiment(SimpleExperiment):
                  """Simple class for loading a file-based PlanOut interpreter experiment"""
                  __metaclass__ = ABCMeta

                  filename = None

                  def assign(self, params, **kwargs):
                    jsondata = json.loads(self.filename)
                    procedure = Interpreter(jsondata, self.salt, kwargs)
                    params.update(procedure.get_params())

                class ExpPlanoutScript(SimpleInterpretedExperiment):
                    filename = strat.planoutJson

                # Pega o profile do usuario
                profUser = UserProfile.objects.get(user=user)
                IDADE = date.today().year-profUser.year_of_birth
                CIDADE = profUser.city
                PAIS = profUser.country.code
                INSTRUCAO = profUser.level_of_education
                SEXO = profUser.gender

                print "Variáveis passadas: ", IDADE, ' ', CIDADE, ' ', PAIS, ' ', INSTRUCAO, ' ', SEXO

                # Tem que pegar todos os dados do profile do usuário a cidade nao funciona muito bem NEED more work
                exp = ExpPlanoutScript(userid=user.id,  CHOICES=CHOICESG, IDADE=IDADE,  CIDADE=CIDADE, PAIS=PAIS, INSTRUCAO=INSTRUCAO,  SEXO=SEXO)
                conversao = False
                deuerro = False
                bloco = -1

            except:
                deuerro = True
                print "Erro nesta randomização"

            # adicionei isso para o fatorial design com PlanOut script
            try:
                f1 = exp.get('fat1')
                f2 = exp.get('fat2')

                fat1=int(f1)
                fat2=int(f2)

                if fat1==1 and fat2==1:
                    ver=0
                elif fat1==2 and fat2==2:
                    ver=1
                elif fat1==1 and fat2==2:
                    ver=2
                elif fat1==2 and fat2==1:
                    ver=3

                # Internamente ainda funciona com versoes A, B, C e D
                if ver == 0:
                    versao ='A'
                elif ver == 1:
                    versao = 'B'
                elif ver == 2:
                    versao = 'C'
                else:
                    versao = 'D'

                URLChoice = CHOICESG[ver]

                achei = True
                conversao = True
                deuerro = False
            except:
                print "Erro no Fatorial:"



        try:
            if len(URLChoice) == 0:
                URLChoice = exp.get('URL')
        except:
            print "Unexpected error1:", sys.exc_info()[0]

        # Houver um erro em algumas das randomizações
        if len(URLChoice) == 0:
            class UrlExperiment(SimpleExperiment):
                def assign(self, params, userid):
                    params.URL = UniformChoice(choices=CHOICESG, unit=userid)

            exp = UrlExperiment(userid=user.id)

            try:
                URLChoice = exp.get('URL')
                bloco=-3
            except:
                print "Unexpected error3:", sys.exc_info()[0]

        num = -1

        if conversao == False:
            num = CHOICES.index(URLChoice)

        if num == 0 and conversao == False :
            versao = 'A' # Removi o balanceamento de 50 50

        elif num == 1 and conversao == False:
            versao = 'B'
        elif conversao == False:
            versao = 'C'
        print "Here2"

        # Um usuário que escolhe uma versão
        # estará nela para sempre
        # e todo o sempre

        try:

            if curso:
                if ExpPart.strategy.strategyType != "crossover" and ExpPart.strategy.strategyType != "cluster":
                    expsCurso = ExperimentDefinition.objects.filter(course=curso)

                    print "tamanho: ", len(expsCurso)

                    for experi in expsCurso:
                        userChoice = UserChoiceExperiment.objects.filter(userStudent=user, experimento=experi)

                        print "Len UserChoice: ", len(userChoice)

                        if len(userChoice) > 0:
                            for usrC in userChoice:
                                versao = usrC.versionExp.version
                                print "EU JA ESCOLHI UMA VERSAO QUE E: ", usrC.versionExp.version


        except:
            print "Erro ao pegar uma versão anterior"
            print "Versão: ", versao

        # Grava a versão escolhida
        userVersion = UserChoiceExperiment()
        userVersion.userStudent = user
        userVersion.bloco = bloco # Vai depender do algoritmo
        userVersion.versionExp = options[versao]
        userVersion.experimento = urlExp.experimento

        verCads = UserChoiceExperiment.objects.filter(experimento=urlExp.experimento, userStudent=user)

        if len(verCads) > 0:
            cont = 0
            for verCad in verCads:
                if cont > 1:
                    print "Deleting ", cont
                    verCad.delete()
                else:
                    userVersion = verCad

                cont = cont+1
        else:
            userVersion.save()



        if userVersion.versionExp.sectionExp_url == URL:
            print "Quarto"
            return True
        else:
            print "Quinto"
            return False
    except:
        print "Sexto", sys.exc_info()[0]
        return False



def cadGrupo(groupUser, groups, exp, userid):

    # Load arms to find the Arm with Less Groups
    opcs = OpcoesExperiment.objects.filter(experimento=exp)
    arms = {}
    for opc in opcs:
        arms[opc.version] = 0


    # grupo -1 deste experimento e o que nao atendeu a nenhum criterio
    grupoMenos1 = None
    listToRandomize = []

#    for arm in arms:
    # Conta quantos As e Bs
    for g in groups:
        # Somente quem nao tem grupo que ira ficar de fora da randomização
        if g.grupos != None:
            listToRandomize.append(g.id)

        if g.versao != None :
            arms[g.versao.version] += 1 # Conta somente os que ja foram randomizados
        elif g.grupos == None:
            grupoMenos1 = g


    print "Arms: ", arms, " listtorandomize: ", listToRandomize


    # Sort Arms
    sortList = sorted(arms.items(), key=lambda x: (x[1], x[0]))

    # Sempre pega o Arm que tem menos usuarios
    armRandomize = sortList[0]
    versao = armRandomize[0]

    print "Sorted list: arm  ", armRandomize
    print "Sorted list: ", sortList

    # Se o usuario tiver -1 iremos cadastrá-lo com no Arm com menos grupos
    if groupUser == -1:
        achei = True
        conversao = True
        deuerro = False

        if grupoMenos1 != None:
            if grupoMenos1.versao != None:
                # So cadastra um arm de acordo com a variavel Versao
                opc = OpcoesExperiment.objects.get(experimento=exp, version=versao)
                grupoMenos1.versao = opc
                grupoMenos1.save()
        else:
            opc = OpcoesExperiment.objects.get(experimento=exp, version=versao)
            g = GroupsCluster()
            g.experiment = exp
            g.versao = opc
            g.save()

        return versao, achei, conversao, deuerro
    # Precisa cadastrar o Grupo != -1
    else:

        MyGroup = GroupsCluster.objects.get(pk=groupUser)

        grupo = -10

        # Randomiza os grupos
        while MyGroup.id != grupo:
            class UrlExperimentCluster(SimpleExperiment):
                def assign(self, params, userid):
                    params.GRUPO = UniformChoice(choices=listToRandomize, unit=userid)

            try:
                randExp = UrlExperimentCluster(userid=userid)
                grupo = int(randExp.get('GRUPO'))

                print "Userid: ", userid, " grupo: ", grupo

                # Cadastra o grupo com a versao
                g = GroupsCluster.objects.get(pk=grupo)
                print "ok1 ", exp.id, " Versao: ", versao
                opc = OpcoesExperiment.objects.get(experimento=exp, version=versao)
                print "ok2"
                g.versao = opc
                g.save()
                print "Versao: ", versao
            except:
                print 'Erro'

            if grupo != groupUser:
                # Primeiramente se o usuario tb pertence a este grupo
                listToRandomize.pop(listToRandomize.index(grupo))

                # Aumenta a quantidade de grupos nesta versao
                arms[versao] += 1
                sortList = sorted(arms.items(), key=lambda x: (x[1], x[0]))
                # Sempre pega o Arm que tem menos usuarios
                armRandomize = sortList[0]
                versao = armRandomize[0]
            else:
                achei = True
                conversao = True
                deuerro = False

        print "Versao: ", versao
        print "Achei: ", achei
        print "Conversao: ", conversao
        print "Deuerro: ", deuerro

        return versao, achei, conversao, deuerro


def VerABprint(URL, user):
    """
    Esta função permite verificar se uma dada URL pode ser mostrada no LMS. Caso ainda tenha ocorrido a randomização
    será chamado a função cadastraVersao em que será randomizado e cadastrado no banco de dados.

    :param URL: endereço usado no LMS
    :param user:  usuário que fez a requisição
    :return: False não mostra o conteúdo e true mostra o conteúdo no LMS
    """
    try:
        """
        Todos os usuários Staffs tem acesso a todas as versões dos usuários.
        """
        try:
            usr = User.objects.get(pk=user.id)
            if usr.is_staff:
                return True
        except:
            print "Erro pegar o usuario"


        # Procura na base de dados para ver se a URL informada faz parte de um Experimento
        print "URL testada", URL, "Usuario: ", user
        urlExp = OpcoesExperiment.objects.get(sectionExp_url=URL)

        expsChoices = UserChoiceExperiment.objects.filter(experimento=urlExp.experimento, userStudent=user)

        if len(expsChoices) > 1:
            cont=0
            for expsC in expsChoices:
                if cont > 0:
                    print "Deletei ", cont
                    expsC.delete()

                cont  = cont + 1

        # Se faz parte, procura-se na base de dados pela URL
        # Verifica se esta URL foi escolhida pelo usuario
        try:
            # Se o experimento desta URL já foi escolhida pelo aluno como
            # Só será considerado TRUE se for igual a URL

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
            if len(expsChoices) == 0:
                # Neste ponto o usuário não o selecionou uma opção, então deve-se
                # Atribuir a este usuário uma versão
                print "Cadastrando com thread 2"
                return cadastraVersao(user,URL,urlExp)
            else:
                return False


    except:
        print "Caso a URL não pertença a nenhum experimento"

        return True

def pulaURL(URL, user):
    """
    Esta função verifica se uma dada URL deve ser pulada. Uma função que pode ser pulada faz parte do experimento, contudo não é a
    atribuida ao usuário na randomização.

    :param URL: url do LMS
    :param user: usuario que fez a requisição
    :return: true -- esta URL não será considerada na hora de renderizar um componente
             false -- quer dizer que não precisa pular e a url será renderizada
    """
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
    """
    Procura por todas as urls que o usuário não escolheu dentre todos os experimentos.

    :param user: usuario que faz a requisicao da função em progress
    :return: lista de todas as URLs que não devem ser contabilizadas na hora de gerar o gráfico com o progresss do LMS
    """
    listURLandExps=[]

    # Pega todos os experimentos que o usuario participou
    expUser = UserChoiceExperiment.objects.filter(userStudent=user)

    # len > 1
    if len(expUser) > 0:
        # Agora tem que pegar as URLs associadas ao usuario

        for exPart in expUser:

            # Pega todas as urlS dos experimentos que o usuario participou
            listURLSeXPS = OpcoesExperiment.objects.filter(experimento=exPart.experimento)

            if len(listURLSeXPS) > 0:
                for urlsEXP in listURLSeXPS:
                    # Adiciona todos exceto as que o usuario escolheu
                    if exPart.versionExp.sectionExp_url != urlsEXP.sectionExp_url:
                        listURLandExps.append(urlsEXP.sectionExp_url)

        return listURLandExps

    else:
        return listURLandExps


def ExcluirDiscussion(user, locationCourse):
    """
     Verifica quais IDs (dos usuários) devem ser excluidos do forum e mais os ID's anônimos que devem ser excluidos.
     Como na listagem não tem como identificar uma simples postagem, foram adicionados uma entidade que conterá os ID's dos comentários.

    :param user: usuário do aluno
    :param locationCourse: location Course
    :return comentarioRemove: retorna uma lista dos IDS dos usuarios que devem ser removidos
    """

    # Pega todos os experimentos deste curso
    exps = ExperimentDefinition.objects.filter(course=locationCourse)

    # todas as versoes
    idsRemove = []
    commentsAnonymous = []

    for exp in exps:
        opcs = OpcoesExperiment.objects.filter(experimento=exp)
        for opc in opcs:
            # Verifica se o usuário selecionou esta versao
            try:
                choice = UserChoiceExperiment.objects.get(versionExp=opc, userStudent=user)
            except:
                # Adiciona todas as versoes que o usuario nao adicionou
                choices = UserChoiceExperiment.objects.filter(versionExp=opc)
                for choice in choices:
                    idsRemove.append(""+str(choice.userStudent.id))

                    # Para este usuario adiciona-se os ids anonymos
                    commentAns = AnonyMousPost.objects.filter(user=choice.userStudent.id)
                    for commentAn in commentAns:
                        commentsAnonymous.append(commentAn.commentid)


    return idsRemove, commentsAnonymous

