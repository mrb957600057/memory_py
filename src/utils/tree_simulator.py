import sys
import os

import numpy as np

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from kernel.belief_tracker import BeliefTracker
from graph.belief_graph import Graph
import memory.config as m_config
from utils.translator import Translator

grandfatherdir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parentdir)
sys.path.append(grandfatherdir)

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, parentdir)

translator = Translator()

def gen_sessions(belief_tracker, output_files):
    """
    :param belief_tracker:
    :param output_files: candidate_files, train, val, test
    :return:
    """
    belief_graph = belief_tracker.belief_graph
    """
    主要逻辑
    :return:
    """
    def gen_random_slot_values(required_field):
        slot_values_mapper = dict()
        num_rnd_external_max = 2
        if required_field == 'virtual_category':
            nodes = belief_graph.get_nodes_by_slot(required_field)
            # choose one
            node = np.random.choice(nodes)
            slot_values_mapper[node.slot] = node.value
            return slot_values_mapper
        if required_field == 'category':
            if belief_tracker.search_node == belief_graph:
                nodes = belief_graph.get_nodes_by_slot(required_field)
                node = np.random.choice(nodes)
            else:
                children_names = belief_tracker.search_node.get_children_names_by_slot(
                    required_field)
                # choose one
                name = np.random.choice(children_names)
                slot = belief_tracker.search_node.get_slot_by_value(name)
                slot_values_mapper[slot] = name
                node = belief_tracker.search_node.get_node_by_value(name)
            slot_values_mapper[node.slot] = node.value
            fields = list(node.fields.keys())
            if 'ac.power' in fields:
                fields.remove('ac.power')
                fields.append('ac.power_float')
            n = np.random.randint(
                0, np.min([len(fields), num_rnd_external_max]) + 1)
            # fields = list(belief_tracker.requested_slots)

            picked_fields = np.random.choice(fields, n).tolist()
            # picked_fields = set()
            # for i in range(n):
            #     if np.random.uniform() < 0.25 and 'brand' in fields:
            #         picked_fields.add('brand')
            #         continue
            #     if 'brand' in picked_fields and np.random.uniform() < 0.1:
            #         picked_fields.add(np.random.choice(fields))
            for f in picked_fields:
                value = random_property_value(f, node)
                # weird
                if value != 'range' and belief_graph.is_entity_value(value):
                    slot_values_mapper['entity'] = value
                else:
                    slot_values_mapper[f] = value
            return slot_values_mapper

        my_search_node = belief_tracker.search_node

        fields = list(belief_tracker.requested_slots)
        n = np.random.randint(
            0, np.min([len(fields), num_rnd_external_max]) + 1)

        picked_fields = np.random.choice(fields, n).tolist()
        # append required fields
        picked_fields.append(required_field)
        picked_fields = set(picked_fields)
        for f in picked_fields:
            value = random_property_value(f, my_search_node)
            # weird
            if value != 'range' and belief_graph.is_entity_value(value):
                slot_values_mapper['entity'] = value
            else:
                slot_values_mapper[f] = value
        return slot_values_mapper

    def gen_ambiguity_response(availables):
        availables = availables[0].replace(
            'api_call_request_ambiguity_removal_', '').split(",")
        pick = np.random.choice(availables)
        slot_values_mapper = dict()
        num_rnd_external_max = 1
        if len(belief_graph.get_nodes_by_value(pick)) > 0:
            slot_values_mapper[belief_graph.get_nodes_by_value(pick)[
                0].slot] = pick
        else:
            slot_values_mapper['ambiguity_removal'] = belief_graph.slots_trans[pick]
        # my_search_node = belief_tracker.ambiguity_slots[pick].parent_node
        #
        # fields = list(my_search_node.fields.keys())
        # n = np.random.randint(0, np.min([len(fields), num_rnd_external_max]) + 1)
        #
        # picked_fields = np.random.choice(fields, n).tolist()
        # # append required fields
        # # picked_fields.append(required_field)
        # for f in picked_fields:
        #     value = random_property_value(f, my_search_node)
        #     slot_values_mapper[f] = value
        return slot_values_mapper

    def render_rhetorical(slot):
        """
        'user': {
            'brand': ['你们这都有什么牌子？', '品牌都有哪些？'],
            'category': ['你们这儿都卖什么种类？', '种类都有哪些？'],
            'price': ['都有哪些价格？', '都有什么价啊？']
        },
        :param slot:
        :return:
        """
        template = ["你们这都有什么<fill>", "<fill>都有哪些", "你们这儿都卖什么<fill>",'你有什么<fill>','你有哪些<fill>']
        trans = belief_graph.slots_trans[slot]
        t = np.random.choice(template)
        if np.random.uniform() < 0.5:
            t = t.replace("<fill>", trans)
        else:
            t = t.replace("<fill>", "")
        cls = "api_call_rhetorical_" + slot
        return t, cls

    def gen_ambiguity_initial():
        slot_values_mapper = dict()
        nodes_value_list = list(belief_tracker.belief_graph.node_header.keys())
        while True:
            key = np.random.choice(nodes_value_list)
            nodes = belief_tracker.belief_graph.get_nodes_by_value(key)
            if len(nodes) == 1 or not belief_graph.is_entity_value(key):
                node = nodes[0]
                if node.slot == 'category' or node.slot == 'virtual_category':
                    continue
                slot_values_mapper[node.slot] = node.value
                break
            slot_values_mapper['entity'] = key
            break
        if np.random.uniform() < 0.25:
            node = np.random.choice(nodes)
            slot_values_mapper[node.parent_node.slot] = node.parent_node.value
        # slot_values_mapper.clear()
        # slot_values_mapper['entity'] = '4G'
        return slot_values_mapper

    def random_property_value(field, search_node):
        if field == 'price':
            value = 'range'
            # if np.random.uniform() < 0.3:
            #     if np.random.uniform() < 0.5:
            #         value += '元'
            #     else:
            #         value += '块'

            return value

        # if field == 'ac.power':
        #     value = 'range'
        #
        #     if np.random.uniform() < 0.5:
        #         value += 'P'
        #     else:
        #         value += '匹'
        #
        #     return value
        if field == 'ambiguity_removal':
            value = np.random.choice(list(belief_tracker.ambiguity_slots.keys()))
            # nodes = belief_graph.get_nodes_by_value(value)
            # if len(nodes) > 0:
            #     slot = nodes[0].slot
            #     del slot_values_mapper[field]
            #     slot_values_mapper[slot] = value
            return value

        if belief_graph.get_field_type(field) == 'range':
            # return search_node.get_node_slot_trans(field) + 'range'
            return 'range'
        else:
            return np.random.choice(search_node.get_children_names_by_slot(field))

    def get_avail_brands(category):
        category_node = belief_graph.get_nodes_by_value(category)[0]
        brands = category_node.get_children_names_by_slot('brand')
        return brands

    def get_requested_field():
        requested = np.random.choice(
            ['virtual_category', 'category', 'property', 'ambiguity_removal'], p=[0.1, 0.8, 0.1, 0])
        return requested

    def render_thesaurus(v, thesaurus):
        if v in thesaurus:
            choice = thesaurus[v][:]
            choice.append(v)
            v = np.random.choice(choice)
        return v

    def render_lang(slot_values_mapper, fresh, thesaurus):
        search_node = belief_tracker.search_node
        prefix = ['', '我来买', '我来看看', '看看', '我要买', '我想买','有没有']
        postfix = ['吧', '呢', '']
        lang = np.random.choice(prefix)
        if 'brand' in slot_values_mapper:
            lang += slot_values_mapper['brand'] + \
                np.random.choice(['的', ''], p=[0.7, 0.3])
        if 'price' in slot_values_mapper:
            lang += np.random.choice(['价格', '价位', '']) + \
                slot_values_mapper['price']
            if np.random.uniform() < 0.3:
                if np.random.uniform() < 0.5:
                    lang += '元'
                else:
                    lang += '块'
        if 'category' in slot_values_mapper:
            lang += slot_values_mapper['category'] + ','

        for k, v in slot_values_mapper.items():
            if k in ['brand', 'price', 'category']:
                continue
            if k not in ['entity', 'ambiguity_removal'] and belief_graph.get_field_type(k) == 'range':
                trans = search_node.get_node_slot_trans(k)
                if fresh or 'range' in lang:
                    lang += trans + 'range'
                    if k in ['tv.size', 'phone.size', 'pc.size']:
                        lang += '寸'
                    if k in ['tv.distance']:
                        lang += '米'
                    if k in ['ac.power_float']:
                        lang += np.random.choice(['p', '匹'])
                else:
                    lang += trans + 'range'
                    if k in ['tv.size', 'phone.size']:
                        lang += '寸'
                    if k in ['tv.distance']:
                        lang += '米'
                    if k in ['ac.power_float']:
                        lang += np.random.choice(['p', '匹', ''])
            else:
                if v in ['电视', '冰箱', '空调','电脑']:
                    if v == '电视':
                        v = np.random.choice(['电视','电视机','彩电'])
                    if v == '冰箱':
                        v = np.random.choice(['冰箱','电冰箱'])
                    if v == '电脑':
                        v = np.random.choice(['pc', '电脑','计算机'])
                    v = np.random.choice(['台','一台','一个','个','']) + v
                if v in ['手机']:
                    v = np.random.choice(['部', '一部', '一个', '个', '']) + v
                if v in thesaurus:
                    choice = thesaurus[v][:]
                    choice.append(v)
                    v = np.random.choice(choice)
                lang += v + ","

        if lang[-1] == ',':
            lang = lang[0:-1]
        lang = lang + np.random.choice(postfix, p=[0.1, 0.1, 0.8])
        lang = lang.lower()
        if 'root' in lang:
            lang = np.random.choice(['我来买东西', '购物', '买点东西'])
        return lang

    def render_cls(slot_values_mapper):
        params = []
        for key in sorted(slot_values_mapper.keys()):
            params.append(key + ":" + slot_values_mapper[key])
        return 'api_call_slot_' + ','.join(params)

    def render_api(api):
        return api[0]

    def render_deny():
        prefix = np.random.choice(['我不要', '不要', '不要这个', '不想要'])
        lang = prefix
        cls = 'api_call_deny_all'
        if 'brand' in belief_tracker.filling_slots:
            if np.random.uniform() < 0.7:
                lang += belief_tracker.filling_slots['brand']
                cls = 'api_call_deny_brand'
        return lang, cls, 'placeholder'

    requested = get_requested_field()
    i = 0

    thesaurus =  dict()
    with open('../../data/gen_product/thesaurus.txt', 'r') as f:
        for line in f:
            line = line.strip('\n')
            key, value = line.split('#')
            thesaurus[key] = value.split(',')

    candidates = set()
    api_set = set()
    train_set = []
    test_set = []
    val_set = []
    train_gbdt = set()

    container = []
    flow_container = []
    single_container = []
    duplicate_removal = set()
    flow_removal = set()
    flows = list()
    mapper = {'train': train_set, 'val': val_set, 'test': test_set}
    which = np.random.choice(['train', 'val', 'test'], p=[0.8, 0.1, 0.1])
    fresh = True
    with_multiple = False
    mlt_container = []
    mlt_candidates = []
    with_qa = True
    with_deny = True
    while 1:
        if requested == 'property':
            slot_values_mapper = gen_ambiguity_initial()
        elif requested == 'ambiguity_removal':
            slot_values_mapper = gen_ambiguity_response(
                belief_tracker.issue_api(attend_facet=False))
        else:
            slot_values_mapper = gen_random_slot_values(
                required_field=requested)
        belief_tracker.color_graph(
            slot_values_mapper=slot_values_mapper, range_render=False)
        user_reply = render_lang(slot_values_mapper, fresh, thesaurus)
        if not fresh:
            gbdt = 'plugin:' + 'api_call_slot' + '|'\
                + '|'.join([key + ":" + value for key, value in slot_values_mapper.items()])\
                + '#' + requested + '$' + user_reply
        else:
            gbdt = 'plugin:' + 'api_call_slot' + '|'\
                + '|'.join([key + ":" + value for key, value in slot_values_mapper.items()]) \
                   + '#' + user_reply

        gbdt = gbdt.lower()
        train_gbdt.add(gbdt)

        fresh = False
        cls = render_cls(slot_values_mapper)
        candidates.add(cls.lower())
        api = render_api(belief_tracker.issue_api(attend_facet=False))
        line = user_reply + '\t' + cls + '\t' + api
        flow = cls + '\t' + api
        if requested == 'category':
            single_container.append(line)
            single_container.append('')
        requested = belief_tracker.get_requested_field()
        trans_api = translator.en2cn(api)
        if not api.startswith('api_call_search'):
            api_set.add(api + '##' + trans_api)
        container.append(line.lower())
        flow_container.append(flow.lower())
        if api.startswith('api_call_search'):
            if np.random.uniform() < 0.4:
                a, b, c = render_deny()
                candidates.add(b)
                container.append('\t'.join([a, b, c]))
        mlt_line = user_reply + '\t' + 'plugin:apl_call_slot,' +\
            '|'.join([key + ":" + value for key, value in slot_values_mapper.items()])\
            + '\t' + api
        mlt_container.append(mlt_line)

        if with_qa:
            filling_slots = belief_tracker.filling_slots
            if 'category' in filling_slots:
                if np.random.uniform() < 0.25:
                    qa = np.random.choice([render_thesaurus(filling_slots['category'], thesaurus), ''])\
                         + np.random.choice(['在哪里', '在什么地方', '在几楼'])
                    line = qa + '\t' + 'api_call_query_location_' + 'category:'\
                           + filling_slots['category'] + '\t' + 'placeholder'
                    flow = 'api_call_query_location_' + 'category:'\
                           + filling_slots['category'] + '\t' + 'placeholder'
                    container.append(line)
                    # flow_container.append(flow.lower())
                    candidates.add('api_call_query_location_' + 'category:'\
                           + filling_slots['category'])
                if np.random.uniform() < 0.25:
                    brands = get_avail_brands(filling_slots['category'])
                    if brands:
                        brand = np.random.choice(brands)
                        qa = brand + np.random.choice([render_thesaurus(filling_slots['category'], thesaurus), '的', ''])\
                             + np.random.choice(['多少钱', '什么价格'])
                        line = qa + '\t' + 'api_call_query_price_' + 'brand:'\
                               + brand + ',' + 'category:' + filling_slots['category'] + '\t' + 'placeholder'
                        flow = 'api_call_query_price_' + 'brand:'\
                               + brand + ',' + 'category:' + filling_slots['category'] + '\t' + 'placeholder'
                        # flow_container.append(flow.lower())
                        container.append(line)
                        candidates.add('api_call_query_price_' + 'brand:'\
                               + brand + ',' + 'category:' + filling_slots['category'])

                # ask brand of category
                if np.random.uniform() < 0.25:
                    brands = get_avail_brands(filling_slots['category'])
                    if brands:
                        brand = np.random.choice(brands)
                        qa = np.random.choice([render_thesaurus(filling_slots['category'], thesaurus), '']) + np.random.choice(['都有哪些品牌', '都有哪些牌子'])
                        line = qa + '\t' + 'api_call_query_brand_category:' + filling_slots['category'] + '\t' + 'placeholder'
                        flow = 'api_call_query_price_' + 'brand:'\
                               + brand + ',' + 'category:' + filling_slots['category'] + '\t' + 'placeholder'
                        # flow_container.append(flow.lower())
                        container.append(line)
                        candidates.add('api_call_query_brand_category:' + filling_slots['category'])

        if requested and requested != 'ambiguity_removal':
            if np.random.uniform() < 0:
                reh, cls = render_rhetorical(requested)
                rhetorical = "plugin:" + cls + '#' + requested + "$" + reh
                memory_line = reh + '\t' + cls + '\t' + 'placeholder'
                flow = cls + '\t' + 'placeholder'
                cls = cls.lower()
                candidates.add(cls)
                memory_line = memory_line.lower()
                container.append(memory_line)
                # flow_container.append(flow.lower())
                train_gbdt.add(rhetorical.lower())
        # print(line)
        if not requested:
            fresh = True
            requested = get_requested_field()
            belief_tracker.clear_memory()
            line = ''
            container.append(line.lower())
            flow_container.append(line.lower())
            # check duplicate
            bulk = '#'.join(container).lower()
            single_bulk = '#'.join(single_container).lower()
            if bulk not in duplicate_removal:
                duplicate_removal.add(bulk)
                mapper[which].extend(container)
                # for a in container:
                #     print(a)
            else:
                print('# duplicate #')
            if single_bulk not in duplicate_removal:
                duplicate_removal.add(single_bulk)
                mapper[which].extend(single_container)

            flow_bulk = '#'.join(flow_container).lower()
            if flow_bulk not in flow_removal:
                flow_removal.add(flow_bulk)
                flows.extend(flow_container)
            which = np.random.choice(
                ['train', 'val', 'test'], p=[0.8, 0.1, 0.1])
            container = []
            single_container = []
            flow_container = []
            # print(line)
            i += 1
            print(i)
            if i >= 60000:
                break

    # lower everything

    # print('writing', len(train_set), len(
    #     val_set), len(test_set), len(candidates))
    #

    with_flow = True
    if with_flow:
        with open(grandfatherdir + '/data/memn2n/train/tree/origin/flow.txt', 'w', encoding='utf-8') as f:
            for line in flows:
                f.writelines(line + '\n')

    with_base = True
    with_gbdt = False
    base_count = 0
    if with_base:
        with open(grandfatherdir + '/data/memn2n/train/base/interactive_memory.txt', encoding='utf-8') as cf:
            for line in cf:
                line = line.strip('\n')
                if not line:
                    base_count += 1

    train_count = 0
    with open(output_files[1], 'w', encoding='utf-8') as f:
        for line in mapper['train']:
            f.writelines(line + '\n')
        if with_base:
            with open(grandfatherdir + '/data/memn2n/train/base/interactive_memory.txt', encoding='utf-8') as cf:
                for line in cf:
                    line = line.strip('\n')
                    if not line:
                        train_count += 1
                        if train_count > 0.7 * base_count:
                            break
                    f.writelines(line + '\n')

    with open(output_files[2], 'w', encoding='utf-8') as f:
        for line in mapper['val']:
            f.writelines(line + '\n')
        if with_base:
            with open(grandfatherdir + '/data/memn2n/train/base/interactive_memory.txt', encoding='utf-8') as cf:
                for line in cf:
                    line = line.strip('\n')
                    if not line:
                        train_count += 1
                        if train_count > 0.8 * base_count:
                            f.writelines(line + '\n')
                        if train_count > 0.9 * base_count:
                            break

    with open(output_files[3], 'w', encoding='utf-8') as f:
        for line in mapper['test']:
            f.writelines(line + '\n')
        if with_base:
            with open(grandfatherdir + '/data/memn2n/train/base/interactive_memory.txt', encoding='utf-8') as cf:
                for line in cf:
                    line = line.strip('\n')
                    if train_count > 0.9 * base_count:
                        f.writelines(line + '\n')

    with_faq = True
    if with_faq:
        faq = set()
        with open(grandfatherdir + '/data/memn2n/train/faq/facility.txt', encoding='utf-8') as cf:
            for line in cf:
                a, b, c = line.strip('\n').split('\t')
                candidates.add(b)
                line = '\t'.join([a, b, 'placeholder'])
                faq.add(line)
            for i in range(1, len(output_files)):
                with open(output_files[i], 'a', encoding='utf-8') as f:
                    for line in faq:
                        f.writelines('\n')
                        f.writelines(line + '\n')

        with open(grandfatherdir + '/data/memn2n/train/faq/discount.txt', encoding='utf-8') as cf:
            for line in cf:
                a, b, c = line.strip('\n').split('\t')
                candidates.add(b)
                line = '\t'.join([a, b, 'placeholder'])
                faq.add(line)
            for i in range(1, len(output_files)):
                with open(output_files[i], 'a', encoding='utf-8') as f:
                    for line in faq:
                        f.writelines('\n')
                        f.writelines(line + '\n')

    # candidate
    if with_base:
        with open(grandfatherdir + '/data/memn2n/train/base/candidates.txt', encoding='utf-8') as cf:
            for line in cf:
                line = line.strip('\n')
                candidates.add(line)
    candidates = list(candidates)
    candidates.sort()
    len_origin = len(candidates)
    if len_origin < m_config.CANDIDATE_POOL:
        for i in range(m_config.CANDIDATE_POOL - len_origin):
            candidates.append('reserved_' + str(i + len_origin))
    with open(output_files[0], 'w', encoding='utf-8') as f:
        for line in candidates:
            f.writelines(line + '\n')

    with open(grandfatherdir + '/data/memn2n/train/tree/api.txt', 'w', encoding='utf-8') as af:
        for line in api_set:
            af.writelines(line + '\n')

    print('writing', len(train_set), len(
        val_set), len(test_set), len_origin, len(candidates), 'base_count:', train_count)

    if not with_gbdt:
        return
    # gbdt
    with open(output_files[4], 'w', encoding='utf-8') as f:
        for line in train_gbdt:
            f.writelines(line + '\n')
        # hello
        with open(grandfatherdir + '/data/memn2n/dialog_simulator/greet.txt',
                  'r', encoding='utf-8') as hl:
            for line in hl:
                line = "plugin:api_call_greet" + '#' + line.strip('\n')
                f.writelines(line + '\n')
        # qa
        # with open(grandfatherdir + '/data/memn2n/dialog_simulator/qa.txt',
        #           'r', encoding='utf-8') as hl:
        #     for line in hl:
        #         line = "plugin:api_call_qa" + '#' + line.strip('\n')
        #         f.writelines(line + '\n')
        # chat
        if with_base:
            with open(grandfatherdir + '/data/memn2n/train/gbdt/chat.txt',
                      'r', encoding='utf-8') as hl:
                for line in hl:
                    line = line.strip('\n')
                    cls, sentence = line.split('#')
                    f.writelines('plugin:api_call_base#' + sentence + '\n')


if __name__ == "__main__":
    graph_dir = os.path.join(grandfatherdir, "model/graph/belief_graph.pkl")
    config = dict()
    config['belief_graph'] = graph_dir
    config['solr.facet'] = 'off'
    # memory_dir = os.path.join(grandfatherdir, "model/memn2n/ckpt")
    log_dir = os.path.join(grandfatherdir, "log/test2.log")
    bt = BeliefTracker(config)

    output_files = ['../../data/memn2n/train/tree/origin/candidates.txt',
                    '../../data/memn2n/train/tree/origin/train.txt',
                    '../../data/memn2n/train/tree/origin/val.txt',
                    '../../data/memn2n/train/tree/origin/test.txt',
                    '../../data/memn2n/train/gbdt/train.txt']

    gen_sessions(bt, output_files)
