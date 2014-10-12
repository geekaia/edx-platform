# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.views.decorators.http import require_GET
import logging
from uuid import uuid4
from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
import datetime

from edxmako.shortcuts import render_to_response
from django_future.csrf import ensure_csrf_cookie
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.inheritance import own_metadata
# from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.modulestore import Location
from util.json_request import expect_json, JsonResponse
from contentstore.utils import get_modulestore, get_lms_link_for_item
from contentstore.views.access import has_course_access
from experiments.models import *
from models.settings.course_grading import CourseGradingModel
from contentstore.utils import compute_publish_state
from contentstore.views.helpers import _xmodule_recurse
from django.http import HttpResponse
import csv
from experiments.models import *
from django.contrib.auth.decorators import login_required
# New EDX
from opaque_keys.edx.keys import UsageKey, CourseKey

from django_future.csrf import ensure_csrf_cookie
from django.core.context_processors import csrf

from experiments.models import *
import json

# from contentstore.utils import (
#     get_lms_link_for_item, add_extra_panel_tab, remove_extra_panel_tab,
#     get_modulestore)


__all__ = ['experiments_handler', 'block_clone_handler', 'analise_experiment', 'EmailsExp', 'DefineStrategy']
CREATE_IF_NOT_FOUND = ['course_info']
log = logging.getLogger(__name__)

@require_GET
@login_required
def EmailsExp(request,  course_key_string, idExp=None):
    """
    Returns the list of email addresses for ARM {{define}}, which allows for the instructor to send messages to specific groups

    :param request: httprequest default
    :param idExp: experiment
    :return: CSV file format




    Retorna a lista de e-mails por ARM, o que pode permitir que o professor envie e-mails para um grupo em específico.

    :param request: httprequest default
    :param idExp: ID do experimento
    :return: CSV file format
    """

    usage_key = CourseKey.from_string(course_key_string)

    if not has_course_access(request.user, usage_key):
        raise PermissionDenied()

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="relatorio2.csv"'
    writer = csv.writer(response)

    try:
        exp = ExperimentDefinition.objects.get(userTeacher=request.user, id=idExp)
        expsUsrsInfos={}

        uschs = UserChoiceExperiment.objects.filter(experimento=exp)

        print "Tamanho: ", len(uschs)
        # print "exp: ", exp

        listA = []
        listB = []
        listC = []

        writer.writerow(['arm', 'usuario', 'e-mail'])

        for usch in uschs:
            if usch.versionExp.version == "A":
                listA.append(usch.userStudent)
            elif usch.versionExp.version == "B":
                listB.append(usch.userStudent)
            else:
                listC.append(usch.userStudent)

        for i in listA:
            writer.writerow(['A', i.username, i.email])

        for i in listB:
            writer.writerow(['B', i.username, i.email])

        for i in listC:
            writer.writerow(['C', i.username, i.email])

        return response

    except:
        print "Erro ao pegar o exp"


@ensure_csrf_cookie
@login_required
def DefineStrategy(request,  course_key_string, idExperiment=None):

    """
    Allows for switching among PlanOut operators (UniformChoice and WeightedChoice) as well as specifying an experimental design created through 
    JMP, R or Minitab

    :param request: http request default
    :param course_key_string:
    :param idExperiment: experiment id 
    :return: render pages which allow for strategy definition


    Permite alternar entre os operadores do PlanOut (UniformChoice e WeightedChoice) e especificar um design do experimento criado pelo JMP, R ou Minitab.

    :param request: http request default
    :param course_key_string:
    :param idExperiment: id do experimento
    :return: renderiza a página que pemrite definir a estratégia
    """
    mensagem = ""
    mensagemWeightedChoice = ''
    mensagemUniformChoice=''
    mensagemCustom=''
    mensagemCrossOver=''
    mensagemCluster=''

    usage_key = CourseKey.from_string(course_key_string)

    # print "Course Location: ", courseKey

    if not has_course_access(request.user, usage_key):
        raise PermissionDenied()

    csrf_token = csrf(request)['csrf_token']

    exp = ExperimentDefinition.objects.get(pk=idExperiment)

    strategy = exp.strategy

    try:
        if request.POST:
            strategySel = request.POST['strategySel']
            strategy.strategyType = strategySel


            if strategySel == 'WeightedChoice':

                # monta os percents
                fields = strategy.percents.split(';')
                cont = 0

                maxl = len(fields)
                lista = []

                for i in range(0, maxl):
                    lista.append(str(request.POST['peso'+str(i)]))


                strategy.percents = ';'.join(lista)
                strategy.save()

                mensagemWeightedChoice = "WeightedChoice Salvo!"
            elif strategySel == 'planOut':

                # Este Design ainda não está funcionando apropriadamente
                strategy.planoutScript = request.POST['input']
                strategy.planoutJson = request.POST['output']
                strategy.save()

                mensagemCustom = 'PlanoutScript e Json salvos com sucesso!!'

            elif strategySel == 'UniformChoice':
                strategy.save()

                print "A estratégia é UniformChoice"
                mensagemUniformChoice = "UniformChoice Salvo!"

            elif strategySel == 'customdesign':
                strategy.customDesign = request.POST['customDesign']
                strategy.save()
            elif strategySel == 'fatorial':
                strategy.fatorial = request.POST['fatorial']
                strategy.save()
            elif strategySel == 'crossover':
                strategy.periodos = request.POST['periodos']+''
                print 'ok here'

                try:
                    ExpRel = request.POST['expRel']
                    print "ExpRel: ", ExpRel
                    strategy.periodoRel = ExperimentDefinition.objects.get(pk=int(ExpRel))
                except:
                    print "Error!"
                    strategy.periodoRel = exp

                print 'ok here2 ', strategy.periodoRel.id


                strategy.save()
                print "Design CrossOver saldo com sucesso"

                mensagemCrossOver='Design CrossOver salvo com sucesso!!!'

            elif strategySel == 'cluster':
                print "asdfasdf"
                quantGroups = request.POST['quantG']
                quantCad = GroupsCluster.objects.filter(experiment=exp)

                # Para cada grupo cadastra-se ou atualiza -1 e o codigo para cadastrar
                for i in range(1, int(quantGroups)+1):
                    seq = getSequencia(request, i)
                    idG = request.POST['f'+str(i)]

                    if int(idG) == -1:
                        g = GroupsCluster()
                        g.experiment = exp
                        strG = json.dumps(seq)
                        g.grupos = strG
                        g.save()
                    else:
                        g = GroupsCluster.objects.get(pk=int(idG))
                        strG = json.dumps(seq)
                        g.grupos = strG
                        g.save()

                mensagemCluster='Design CrossOver salvo com sucesso!!!'

                strategy.save()

    except:
        mensagem = 'Ocorreu um erro ao salvar a estratégia!!!'


    pesos = "<br />"
    arms = ['A', 'B', 'C', 'D', 'D', 'F']

    # Render html pesos Weight
    cont = 0
    # Pega a quantidade de versões
    #OpcoesExperiment.objects.filter(experimento=exp.)
    percents = strategy.percents.split(';')

    exps = ExperimentDefinition.objects.filter(course=exp.course)

    opcsSel = []

    for expC in exps:
        if expC.strategy.strategyType == 'crossover':
            opcsSel.append(expC)

    for peso in percents:
        pesos += "Percent Arm "+arms[cont]+" <input type='text' name='peso"+str(cont)+"' class='form-control' value='"+str(peso)+"' /> <br />"
        cont += 1

    linhas = []
    print "ClusterGroups: ", exp.strategy.clusterGroups


    try:


        #GruposJson = json.loads(exp.strategy.clusterGroups)
        clustersG = GroupsCluster.objects.filter(experiment=exp)



        selectsgrupos = ''
        for Line in clustersG:
            linha="<tr id='"+str(Line.id)+"'>"
            row = Line.id
            SEQ = ['0', '3', '6', '9', '12']
            cont = 0
            print "Line: ", line

            try:
                line = json.loads(Line.grupos)
            except:
                print "Other Group"
                continue

            for cond in line:

                if cont != 0:
                    linha += '<td>and</td>'
                else:
                    regId = "<input type='hidden' name=f'"+str(Line.id)+"' value='"+str(Line.id)+"' />"

                if cond['tipo'] == 'sexo':
                    selectsgrupos += "$('#"+SEQ[cont]+"sexo"+str(row)+"').val('"+cond['val']+"'); "
                    linha += "<td>"+regId+"Sexo: <input type='hidden' name='"+SEQ[cont]+"|"+str(row)+"'  value='sexo' /></td>"
                    linha += "<td><select id='"+SEQ[cont]+"sexo"+str(row)+"' name='"+SEQ[cont]+"|sexo|"+str(row)+"'><option value='m'>Masculino</option><option value='f'>Feminino</option></select> </td>"
                elif cond['tipo'] == 'escolaridade':
                    selectsgrupos += "$('#"+SEQ[cont]+"escolaridade"+str(row)+"').val('"+cond['val']+"'); "
                    linha +=  "<td>"+regId+"Escolaridade:  <input type='hidden' name='"+SEQ[cont]+"|"+str(row)+"' value='escolaridade' /> </td>"
                    linha += "<td><select id='"+SEQ[cont]+"escolaridade"+str(row)+"' name='"+SEQ[cont]+"|escolaridade|"+str(row)+"'><option value='p'> Doctorate </option> <option value='m'> Master's or professional degree</option><option value='b'> Bachelor's degree</option> <option value='a'> Associate's degree</option><option value='hs'> Secondary/high school</option> <option value='jhs'> Junior secondary/junior high/middle school</option><option value='el'>Elementary/primary school</option> <option value='none'>None</option> <option value='other'>Other</option> </td>"
                elif cond['tipo'] == 'pais':
                    selectsgrupos += "$('#"+SEQ[cont]+"pais"+str(row)+"').val('"+cond['val']+"'); "
                    from django_countries.countries import COUNTRIES
                    options = ''

                    for country in COUNTRIES:
                        options += "<option value='"+country[0]+"'>"+country[1].encode('utf-8')+"</option>"

                    linha += "<td>"+regId+"Pais: <input type='hidden' name='"+SEQ[cont]+"|"+str(row)+"' value='pais' /> </td>"
                    linha += "<td><select id='"+SEQ[cont]+"pais"+str(row)+"' name='"+SEQ[cont]+"|pais|"+str(row)+"'> "+ options +"</select></td>"
                elif cond['tipo'] == 'age':
                    selectsgrupos += "$('#"+SEQ[cont]+"condage"+str(row)+"').val('"+cond['c_age']+"'); "
                    selectsgrupos += "$('#"+SEQ[cont]+"age"+str(row)+"').val('"+cond['val']+"');"

                    linha += "<td>"+regId+"Age:  <input type='hidden' name='"+SEQ[cont]+"|"+str(row)+"' value='age' /> </td>"
                    linha += "<td><select id='"+SEQ[cont]+"condage"+str(row)+"' name='"+SEQ[cont]+"|condage|"+str(row)+"'> <option value='>'>></option><option value='<'><</option><option value='<='><=</option><option value='>='>>=</option></select> "
                    linha += "<input id='"+SEQ[cont]+"age"+str(row)+"' name='"+SEQ[cont]+"|age|"+str(row)+"' type='number' min='0' max='100'/></td>"
                elif cond['tipo'] == 'city':
                    selectsgrupos += "$('#"+SEQ[cont]+"city"+str(row)+"').val('"+cond['val']+"'); "
                    linha += "<td>"+regId+"City like:  <input type='hidden' name='"+SEQ[cont]+"|"+str(row)+"' value='city' /></td>"
                    linha += "<td><input id='"+SEQ[cont]+"city"+str(row)+"' name='"+SEQ[cont]+"|city|"+str(row)+"' type='text'/></td>"

                cont += 1


            if len(line) != 5: # tamanho maximo
                linha += '<td>and</td>'
                linha += "<td><input type='hidden' name='"+SEQ[cont]+"|"+str(row)+"' value='criteria' /> <select id='"+SEQ[cont]+"col"+str(row)+"'> <option value='gender'>Gender </option> <option value='age'>Age</option><option value='escolaridade'>Escolaridade</option><option value='country'>Country</option><option value='city'>City</option> </select> </td>"
                linha += "<td><input type='button' value='+' onclick='addFactor(this,"+SEQ[cont]+","+str(row)+");'/></td>"

            if len(line) == 1:
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
            elif len(line) == 2:
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'
            elif len(line) == 3:
                linha += '<td></td>'
                linha += '<td></td>'
                linha += '<td></td>'

            linha += "<td><a onClick='upDateLen(this, "+Line.id+");'><i class='fa fa-trash'></i></a></td> </tr>"

            print "\nLinha: ", linha

            linhas.append(linha)

    except:
        import sys
        print "Unexpected error:", sys.exc_info()

    return render_to_response('experiment/estrategia.html', {
            'course_key_string': course_key_string,
            'csrf': csrf_token,
            'idExperiment': idExperiment,
            'strat': strategy,
            'elementosStrat': '',
            'pesos': pesos,
            'mensagem': mensagem,
            'mensagemWeightedChoice': mensagemWeightedChoice,
            'mensagemUniformChoice': mensagemUniformChoice,
            'mensagemCustom': mensagemCustom,
            'mensagemCrossOver': mensagemCrossOver,
            'mensagemCluster': mensagemCluster,
            'exps': opcsSel,
            'periodos': strategy.periodos,
            "expRel": strategy.periodoRel,
            'linhas': linhas,
            'selectsgrupos': selectsgrupos,

        })

def getSequencia(request, linha):
    criterios = [] # Lista com a sequencia

    SEQ = [0, 3, 6, 9, 12]

    for col in SEQ:
        # gera um dicionario com criterios
        try:
            print "Get ", col, '|', linha
            criterio = request.POST[str(col)+'|'+str(linha)]
            print "Criterio", criterio
            crit = {}
            crit['tipo'] = criterio
            crit['val'] = request.POST[str(col)+'|'+criterio+'|'+str(linha)]
            print "Val: ", crit['val']

            if criterio == 'age':
                crit['c_age'] = request.POST[str(col)+'|condage|'+str(linha)]

            if criterio == 'criteria':
                break
            else:
                criterios.append(crit)

        except:
            print 'Nao tem criterio em col: ', col, ' row: ', linha

    return criterios


@require_GET
@ensure_csrf_cookie
@login_required
def experiments_handler(request, course_key_string):
    """
    Displays the experiment list for the current course

    :param request: http request default
    :param course_key_string: slashes:USPx+CS0000+2014_1
    :return: rendered html 


    Mostra a listagem dos experimentos deste curso.

    :param request: http request default
    :param course_key_string: slashes:USPx+CS0000+2014_1
    :return: html renderizado
    """

    usage_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, usage_key):
        raise PermissionDenied()

    course_module = modulestore().get_course(usage_key, depth=3)

    # Lista dos Experimentos
    expList = ExperimentDefinition.objects.filter(userTeacher=request.user, course=course_module.location)
    lms_link = get_lms_link_for_item(course_module.location) # link para o LMS

    return render_to_response('experiment/experimentos.html', {
            'lms_link': lms_link,
            'explist': expList,
            'course_key_string': course_key_string,
            'context_course': course_module # Se não tiver essa variável não carregará o menu
        })


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "PUT", "POST"))
@expect_json
def block_clone_handler(request, course_key_string):
    """

    Permite clonar o conteúdo de uma dada semana do experimento. Além de clonar, nesta função faz a definição do experimento. o que insere entradas nas
    tabelas ExperimentDefinition, StrategyRandomization e OpcoesExperiment.

    :param request: http request com parent_location (location do curso) e mais source_locator (location da section)
    :param course_key_string: useless
    :return: json com OK
    """

    letras = ['A', 'B', 'C', 'D']

    if request.method in ('PUT', 'POST'):
        #  Get location Course com base no valor passado pelo Json
        locatorCursokey = UsageKey.from_string(request.json['parent_locator'])
        locatorSectionKey = UsageKey.from_string(request.json['source_locator'])

        if not has_course_access(request.user, locatorSectionKey):
            raise PermissionDenied()

        # Verifica se já tem um experimento de acordo com o SourceLocation
        expSection = None
        try:
            opcExp = OpcoesExperiment.objects.get(sectionExp='%s' % request.json['source_locator'])
            temExp = True
            expSection = opcExp.experimento # pega o experimento para cadastrar a nova versao
        except:
            temExp = False

        # Pesquisa no banco de dados o Curso do qual duplicará os módulos
        course = modulestore().get_item(locatorCursokey, depth=3)
        sections = course.get_children()
        quantidade = 0

        for section in sections:

            if locatorSectionKey == section.location:
                NewLocatorItemSection = create_item(locatorCursokey, 'chapter', section.display_name_with_default, request)

                # tem que Mudar para HomeWork, ou qualquer tipo que eu definir
                SectionLocation =  NewLocatorItemSection
                descript = get_modulestore(NewLocatorItemSection).get_item(NewLocatorItemSection)

                storeSection = get_modulestore(NewLocatorItemSection)

                try:
                    existing_item = storeSection.get_item(SectionLocation)

                    field = existing_item.fields['start']

                    if section.start is not None:
                        print "NÃO É NULO "
                        field.write_to(existing_item, section.start)

                        storeSection.update_item(existing_item, request.user.id)

                except:
                    print "Start Date and end Date"


                subsections = section.get_children()
                quantidade = 0

                if temExp:
                    opcExp3 = OpcoesExperiment()
                    opcExp3.experimento = expSection
                    opcExp3.sectionExp = "%s" % NewLocatorItemSection
                    opcExp3.sectionExp_url = '%s' % getURLSection(locatorCursokey, NewLocatorItemSection)

                    lenOpcs = len(OpcoesExperiment.objects.filter(experimento=expSection))

                    opcExp3.version = letras[lenOpcs]
                    opcExp3.save()

                    st = opcExp3.experimento.strategy
                    st.percents +=';0.0'
                    st.save()

                else:
                    st = StrategyRandomization()
                    st.strategyType = 'UniformChoice'
                    st.percents = '0.0;0.0'
                    st.save()

                    # Experiment defintion
                    exp = ExperimentDefinition()
                    exp.course = request.json['parent_locator']
                    exp.userTeacher = request.user
                    now = datetime.datetime.now()
                    exp.descricao='MyExperiment %s ' % now
                    exp.strategy = st
                    exp.save()

                    # Define a primeira versão do experimento
                    opcExp = OpcoesExperiment()
                    opcExp.experimento = exp
                    opcExp.sectionExp = "%s" % locatorSectionKey
                    opcExp.sectionExp_url = "%s" % section.url_name
                    opcExp.version = 'A'
                    opcExp.save()

                    # Define a segunda versão do experimento
                    opcExp2 = OpcoesExperiment()
                    opcExp2.experimento = exp
                    opcExp2.sectionExp = "%s" % NewLocatorItemSection
                    opcExp2.sectionExp_url = '%s' % getURLSection(locatorCursokey, NewLocatorItemSection)
                    opcExp2.version = 'B'
                    opcExp2.save()

                for subsection in subsections:
                    print
                    print
                    print "Clonando SubSeção: ", subsection.location

                    NewLocatorItemSubsection = create_item(NewLocatorItemSection, 'sequential', subsection.display_name_with_default, request)

                    # Agora iremos testar os Units
                    units_Subsection = subsection.get_children()


                    print "Information about the subsection: "
                    print "subsection.format: ", subsection.format
                    print "subsection.start: ", subsection.start
                    print "Subsection locator: ", NewLocatorItemSubsection

                    # tem que Mudar para HomeWork, ou qualquer tipo que eu definir
                    # subLocation = loc_mapper().translate_locator_to_location(NewLocatorItemSubsection)

                    # print "vert Location: ", subLocation
                    # old_location = course_location.replace(category='course_info', name=block)
                    #
                    #
                    descript = get_modulestore(NewLocatorItemSubsection).get_item(NewLocatorItemSubsection)
                    print "Descript: ", descript

                    CourseGradingModel.update_section_grader_type(descript, subsection.format, request.user)

                    # Start Value
                    storeSection = get_modulestore(NewLocatorItemSubsection)

                    try:
                        existing_item = storeSection.get_item(NewLocatorItemSubsection)

                        field = existing_item.fields['start']

                        if subsection.start is not None:
                            print "NÃO É NULO "
                            field.write_to(existing_item, subsection.start)

                            storeSection.update_item(existing_item, request.user.id)

                    except:
                        print "Deu erro"

                    # Print all Units
                    for unit in units_Subsection:

                        originalState = compute_publish_state(unit)
                        destinationUnit = duplicate_item(NewLocatorItemSubsection, unit.location, unit.display_name_with_default, request.user)


                        # Nesta parte faz-se a leitura se e privado ou publico, se publico, seta a variavel como publico
                        try:

                            print "Vou fazer o translation -- destinationUnit ", destinationUnit

                            # unitLocation = loc_mapper().translate_locator_to_location(destinationUnit)
                            unitLocation = destinationUnit
                            print "unity location: ", unitLocation


                            # Start Value
                            storeUnit = get_modulestore(unitLocation)
                            print "STORE UNIT"

                            try:
                                existing_itemUnit = storeUnit.get_item(unitLocation)

                            except:
                                print "Deu erro"

                            print "Antes do public"

                            if originalState == 'public':
                                def _publish(block):
                                    # This is super gross, but prevents us from publishing something that
                                    # we shouldn't. Ideally, all modulestores would have a consistant
                                    # interface for publishing. However, as of now, only the DraftMongoModulestore
                                    # does, so we have to check for the attribute explicitly.
                                    store = get_modulestore(block.location)
                                    print "Peguei o Store"

                                    if hasattr(store, 'publish'):
                                        store.publish(block.location, request.user.id)

                                _xmodule_recurse(
                                    existing_itemUnit,
                                    _publish
                                )



                        except:
                            print "Erro ao setar publico"

    dataR = {'ok': quantidade }
    #
    return JsonResponse(dataR)





def getURLSection(course_location, loc):
    """
    Retorna a url_name de uma section.

    course_location: endereço do curso
    loc: endereço de uma section
    return: url_name de loc
    """

    curso = modulestore().get_item(course_location, depth=3)
    sections = curso.get_children()

    print "LOC ", loc

    for section in sections:

        if section.location == loc:
            print "Url Name1: ", section.url_name
            return section.url_name


def create_item(parent_location, category, display_name, request, dt_metadata=None, datacomp=None):

    """
    Cria um item no mongoDB de acordo com a categoria especificada.

    :param parent_location: onde sera criado o elemento
    :param category: categoria do experimento sequential, chapter e vertical
    :param display_name: nome que tera o componente criado
    :param dt_metadata: useless
    :param datacomp: useless
    :return: endereço do item criado
    """

    parent = get_modulestore(category).get_item(parent_location)
    dest_location = parent_location.replace(category=category, name=uuid4().hex)

    if not has_course_access(request.user, parent_location):
        raise PermissionDenied()

    metadata = {}
    data = None

    if dt_metadata is not None:
        metadata = dt_metadata
        data = datacomp

    if display_name is not None:
        metadata['display_name'] = display_name

    get_modulestore(category).create_and_save_xmodule(
        dest_location,
        definition_data=data,
        metadata=metadata,
        system=parent.runtime,
    )


    # # TODO replace w/ nicer accessor
    if not 'detached' in parent.runtime.load_block_type(category)._class_tags:
        parent.children.append(dest_location) # Vamos ver se fuciona
        get_modulestore(parent.location).update_item(parent, request.user.id)

    return dest_location


def duplicate_item(parent_location, duplicate_source_location, display_name=None, user=None):
    """
    Duplicate an existing xblock as a child of the supplied parent_location.
    """

    store = get_modulestore(duplicate_source_location)
    source_item = store.get_item(duplicate_source_location)
    # Change the blockID to be unique.
    dest_location = duplicate_source_location.replace(name=uuid4().hex)
    category = dest_location.category

    # Update the display name to indicate this is a duplicate (unless display name provided).
    duplicate_metadata = own_metadata(source_item)
    if display_name is not None:
        duplicate_metadata['display_name'] = display_name
    else:
        if source_item.display_name is None:
            # duplicate_metadata['display_name'] = _("Duplicate of {0}").format(source_item.category)
            duplicate_metadata['display_name'] = source_item.category
        else:
            duplicate_metadata['display_name'] =source_item.display_name

    get_modulestore(category).create_and_save_xmodule(
        dest_location,
        definition_data=source_item.data if hasattr(source_item, 'data') else None,
        metadata=duplicate_metadata,
        system=source_item.runtime,
    )

    dest_module = get_modulestore(category).get_item(dest_location)
    # Children are not automatically copied over (and not all xblocks have a 'children' attribute).
    # Because DAGs are not fully supported, we need to actually duplicate each child as well.
    if source_item.has_children:
        dest_module.children = []
        for child in source_item.children:
            # dupe = duplicate_item(dest_location, Location(child), user=user)
            dupe = duplicate_item(dest_location, child, user=user)
            dest_module.children.append(dupe)
        get_modulestore(dest_location).update_item(dest_module, user.id if user else None)

    if not 'detached' in source_item.runtime.load_block_type(category)._class_tags:
        parent = get_modulestore(parent_location).get_item(parent_location)
        # If source was already a child of the parent, add duplicate immediately afterward.
        # Otherwise, add child to end.
        if duplicate_source_location in parent.children:
            source_index = parent.children.index(duplicate_source_location)
            parent.children.insert(source_index + 1, dest_location)
        else:
            parent.children.append(dest_location)
        get_modulestore(parent_location).update_item(parent, user.id if user else None)

    return dest_location
