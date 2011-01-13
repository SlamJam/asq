'''
slinqer.py A module for LINQ-like facility in Python
'''

import heapq
import itertools
import functools

default = object()

def identity(x):
    return x

def using(iterable):
    return Queryable(iterable)

class Queryable(object):

    def __init__(self, iterable):
        self._iterator = iter(iterable)


    def __iter__(self):
        return self._iterator

    def _create(self, iterable):
        return Queryable(iterable)

    def _create_ordered(self, iterable, direction, func):
        return OrderedQueryable(iterable, direction, func)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        return False

    def close(self):
        pass

    def select(self, selector):
        '''Transforms each element of a sequence into a new form.

        Each element is transformed through a selector function to produce a value for each value in the source
        sequence. The generated sequence is lazily evaluated.

        Args:
            selector: A unary function mapping a value in the source sequence to the corresponding value in the generated
                generated sequence. The argument of the selector function
                (which can have any name) is,

                Args:
                    element: The value of the element

                Returns:
                    The selected value derived from the element value

        Returns:
            A generated sequence whose elements are the result of invoking the selector function on each element of the
            source sequence.
        '''
        return self._create(map(selector, iter(self)))


    def select_with_index(self, selector):
        '''Transforms each element of a sequence into a new form, incorporating the index of the element.

        Each element is transformed through a selector function which accepts the element value and its zero-based index
        in the source sequence. The generated sequence is lazily evaluated.

        Args:
            selector: A two argument function mapping the index of a value in the source sequence and the element value
                itself to the corresponding value in the generated sequence. The two arguments of the selector function
                (which can have any names) and its return value are,

                Args:
                    index: The zero-based index of the element
                    element: The value of the element

                Returns:
                    The selected value derived from the index and element

        Returns:
            A generated sequence whose elements are the result of invoking the selector function on each element of the
            source sequence
        '''
        return self._create(itertools.starmap(selector, enumerate(iter(self))))

    def select_many(self, projector, selector=identity):
        '''Projects each element of a sequence to an intermediate new sequence, flattens the resulting sequence into one
        sequence and optionally transforms the flattened sequence using a selector function.

        Args:
            projector: A unary function mapping each element of the source sequence into an intermediate sequence. If no
                projection function is provided, the intermediate sequence will consist of the single corresponding
                element from the source sequence. The projector function argument (which can have any name) and return
                values are,

                Args:
                    element: The value of the element

                Returns:
                    An iterable derived from the element value

            selector: An optional unary functon mapping the elements in the flattened intermediate sequence to
                corresponding elements of the result sequence. If no selector function is provided, the identity
                function is used.  The selector function argument and return values are,

                Args:
                    element: The value of the intermediate element from the concatenated sequences arising from the
                        projector function.

                Returns:
                    The selected value derived from the element value
        Returns:
            A generated sequence whose elements are the result of projecting each element of the source sequence using
            projector function and then mapping each element through an optional selector function.
        '''
        sequences = (self._create(item).select(projector) for item in iter(self))
        chained_sequence = itertools.chain.from_iterable(sequences)
        return self._create(map(selector, chained_sequence))
        
    def select_many_with_index(self, projector=lambda i,x:[x], selector=identity):
        '''Projects each element of a sequence to an intermediate new sequence, incorporating the index of the element,
        flattens the resulting sequence into one sequence and optionally transforms the flattened sequence using a
        selector function.

        Args:
            projector: A unary function mapping each element of the source sequence into an intermediate sequence. If no
                projection function is provided, the intermediate sequence will consist of the single corresponding
                element from the source sequence. The projector function argument (which can have any name) and return
                values are,

                Args:
                    index: The index of the element in the source sequence
                    element: The value of the element

                Returns:
                    An iterable derived from the element value

            selector: An optional unary functon mapping the elements in the flattened intermediate sequence to
                corresponding elements of the result sequence. If no selector function is provided, the identity
                function is used.  The selector function argument and return values are,

                Args:
                    element: The value of the intermediate element from the concatenated sequences arising from the
                        projector function.

                Returns:
                    The selected value derived from the element value
        Returns:
            A generated sequence whose elements are the result of projecting each element of the source sequence using
            projector function and then mapping each element through an optional selector function.
        '''
        sequences = self.select_with_index(projector)
        chained_sequence = itertools.chain.from_iterable(sequences)
        return self._create(map(selector, chained_sequence))

    def select_many_with_correspondence(self, projector=lambda x:[x], selector=lambda x, y: y):
        '''Projects each element of a sequence to an intermediate new sequence, and flattens the resulting sequence,
        into one sequence and uses a selector function to incorporate the corresponding source for each item in the
        result sequence.

        Args:
            projector: A unary function mapping each element of the source sequence into an intermediate sequence. If no
                projection function is provided, the intermediate sequence will consist of the single corresponding
                element from the source sequence. The projector function argument (which can have any name) and return
                values are,

                Args:
                    source_element: The value of the element

                Returns:
                    An iterable derived from the element value

            selector: An optional unary functon mapping the elements in the flattened intermediate sequence to
                corresponding elements of the result sequence. If no selector function is provided, the identity
                function is used.  The selector function argument and return values are,

                Args:
                    source_element: The corresponding source element

                    element: The value of the intermediate element from the concatenated sequences arising from the
                        projector function.

                Returns:
                    The selected value derived from the element value

        '''

        corresponding_projector = lambda x: (x, projector(x))
        corresponding_selector = lambda x_y : selector(x_y[0], x_y[1])

        sequences = self.select_many(corresponding_projector)
        print(sequences)
        chained_sequence = itertools.chain.from_iterable(sequences)
        return self._create(map(corresponding_selector, chained_sequence))


    def group_by(self, func=identity):
        return self._create(itertools.groupby(self.order_by(func), func))

    def where(self, predicate):
        return self._create(filter(predicate, iter(self)))

    def of_type(self, type):
        return self.where(lambda x: isinstance(x, type))

    def order_by(self, func=identity):
        return self._create_ordered(iter(self), -1, func)

    def order_by_descending(self, func=identity):
        return self._create_ordered(iter(self), +1, func)

    def take(self, n=1):

        def take_result():
            for index, item in enumerate(iter(self)):
                if index == n:
                    break
                yield item

        return self._create(take_result())

    def take_while(self, predicate):
        return self._create(itertools.takewhile(predicate, iter(self)))

    def skip(self, n=1):

        def skip_result():
            for index, item in enumerate(iter(self)):
                if index >= n:
                    yield item

        return self._create(skip_result())

    def skip_while(self, predicate):

        def skip_while_result():
            for item in iter(self):
                if not predicate(item):
                    yield item
                    break

        return self._create(skip_while_result())

    def concat(self, iterable):
        return self._create(itertools.chain(iter(self), iterable))

    def reverse(self):
        lst = list(iter(self))
        lst.reverse()
        return self._create(iter(lst))

    def element_at(self, index):

        def element_at_result():
            for i, item in enumerate(iter(self)):
                if i == index:
                    yield item
                    break

        return self._create(element_at_result())

    def count(self):
        
        index = -1

        for index, item in enumerate(iter(self)):
            pass

        return index + 1

    def any(self, predicate=identity):
        return any(self._create(iter(self)).select(predicate))

    def all(self, predicate=identity):
        return all(self._create(iter(self)).select(predicate))

    def min(self, func=identity):
        return min(self.select(func))

    def max(self, func=identity):
        return max(self.select(func))

    def sum(self, func=identity):
        return sum(self.select(func))

    def average(self, func=identity):
        total = 0
        for index, item in enumerate(iter(self)):
            total += func(item)
        return total / index

    def contains(self, value):
        for item in iter(self):
            if item == value:
                return True
        return False

    def default_if_empty(self, default):
        # Try to get an element from the iterator, if we succeed, the sequence
        # is non-empty. We store the extracted value in a generator and chain
        # it to the tail of the sequence in order to recreate the original
        # sequence.
        try:
            head = next(iter(self))

            def head_generator():
                yield head

            return self._create(itertools.chain(head_generator(), iter(self)))

        except StopIteration:
            # Return a sequence containing a single instance of the default val
            single = (default,)
            return self._create(single)

    def distinct(self, func=identity):

        def distinct_result():
            seen = set()
            for item in iter(self):
                t_item = func(item)
                if t_item in seen:
                    continue
                seen.add(t_item)
                yield item

        return self._create(distinct_result())

    def empty(self):
        return self._create(tuple())

    def difference(self, second_iterable, func=identity):

        def difference_result():
            second_set = set(func(x) for x in second_iterable)
            for item in iter(self):
                if func(item) in second_set:
                    continue
                yield item

        return self._create(difference_result())

    def intersect(self, second_iterable, func=identity):

        def intersect_result():
            second_set = set(func(x) for x in second_iterable)
            for item in iter(self):
                if func(item) in second_set:
                    yield item

        return self._create(intersect_result())

    def union(self, second_iterable, func=identity):
        return self._create(itertools.chain(iter(self), second_iterable)).distinct(func)

    def join(self, inner_iterable, outer_key_func=identity, inner_key_func=identity,
             result_func=lambda outer, inner: (outer, inner)):

        def join_result():
            for outer_item in iter(self):
                outer_key = outer_key_func(outer_item)
                for inner_item in inner_iterable:
                    inner_key = inner_key_func(inner_item)
                    if inner_key == outer_key:
                        yield result_func(outer_item, inner_item)

        return self._create(join_result())

    def first(self):
        return next(iter(self))

    def first_or_default(self, default):
        try:
            return next(iter(self))
        except StopIteration:
            return default

    def last(self):
        sentinel = object()
        result = sentinel

        for item in iter(self):
            result = item

        if item is sentinel:
            raise StopIteration()

        return item

    def last_or_default(self, default):
        sentinel = object()
        result = sentinel

        for item in iter(self):
            result = item

        if item is sentinel:
            return default

        return item

    def aggregate(self, func, seed=default):
        if seed is default:
            return functools.reduce(func, iter(self))
        return functools.reduce(func, iter(self), seed)

    def range(self, start, count):
        return self._create(range(start, start + count))

    def repeat(self, element, count):
        return self._create(itertools.repeat(element, count))

    def zip(self, second_iterable, func=lambda x,y: (x,y)):

        def zip_result():
            second_iterator = iter(second_iterable)
            try:
                while True:
                    x = next(iter(self))
                    y = next(second_iterator)
                    yield func(x, y)
            except StopIteration:
                pass

        return self._create(zip_result)

    def to_list(self):
        lst = list(self)
        # Ideally we would close here
        #self.close()
        return lst

    def to_tuple(self):
        tup = tuple(self)
        # Ideally we would close here
        #self.close()
        return tup

    def as_parallel(self, pool=None):
        from .parallel_queryable import ParallelQueryable
        return ParallelQueryable(self, pool)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return ', '.join(map(repr, self))

class OrderedQueryable(Queryable):

    def __init__(self, iterable, order, func):
        '''
            Args:
                iterable: The iterable sequence to be ordered
                order: +1 for ascending, -1 for descending
                func: The function to select the sorting key
        '''
        assert abs(order) == 1, 'order argument must be +1 or -1'
        super(OrderedQueryable, self).__init__(iterable)
        self._funcs = [ (order, func) ]

    def then_by(self, func=identity):
        self._funcs.append( (-1, func) )
        return self

    def then_by_descending(self, func=identity):
        self._funcs.append( (+1, func) )
        return self
        
    def __iter__(self):
        # A tuple subclass on which we will redefine the __lt__ operator
        # so we can use heapq for complex sorts
        class SortingTuple(tuple):
            pass
            
        # Determine which sorting algorithms to use
        directions = [direction for direction, _ in self._funcs]
        direction_total = sum(directions)
        if direction_total == -len(self._funcs):
            pass
        elif direction_total == len(self._funcs):
            # Uniform descending sort - swap the comparison operators
            SortingTuple.__lt__, SortingTyple.__gt__ = SortingTuple.__gt__, SortingTyple.__lt__
        else:
            # Mixed ascending/descending sort
            def less(lhs, rhs):
                for direction, lhs_element, rhs_element in zip(directions, lhs, rhs):
                    cmp = (lhs_element > rhs_element) - (rhs_element < lhs_element)
                    if cmp == 0:
                        continue
                    if cmp == direction:
                        return True
                return False
            SortingTuple.__lt__ = less

        # Uniform ascending sort - decorate, sort, undecorate using tuple element
        lst = [(SortingTuple(func(item) for _, func in self._funcs), item) for item in self._iterator]
        heapq.heapify(lst)
        while lst:
            key, item = heapq.heappop(lst)
            yield item

    

def my_range(x):
    for i in range(x):
        print("yield {0}".format(i))
        yield i











