#include <sstream>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "edit-distance-inl.h"

namespace py = pybind11;


struct ErrorStats {
    kaldi::int32 ins;
    kaldi::int32 del;
    kaldi::int32 sub;
    kaldi::int32 total;  // minimum total cost to the current alignment.
    std::size_t ref;

    std::string to_string() const {
        std::stringstream ss;
        ss << "ErrorStats(total=" << total
           << ", ins_num=" <<  ins
           << ", del_num=" <<  del
           << ", sub_num=" <<  sub
           << ", ref_num=" <<  ref
           << ")";
        return ss.str();
    }

    static ErrorStats add(const ErrorStats& a, const ErrorStats& b) {
        return {a.ins + b.ins, a.del + b.del, a.sub + b.sub, a.total + b.total, a.ref + b.ref};
    }
};

template <class T>
ErrorStats edit_distance(const std::vector<T> &ref, const std::vector<T>& hyp) {
    ErrorStats e;
    e.total = kaldi::LevenshteinEditDistance(ref, hyp, &e.ins, &e.del, &e.sub);
    e.ref = ref.size();
    return e;
}

template <class T>
struct Alignment {
    T eps;
    std::vector<std::pair<T, T>> alignment;
    kaldi::int32 distance;
};

template <class T>
Alignment<T> align(const std::vector<T>& a, const std::vector<T>& b, T eps) {
    Alignment<T> ret = {eps};
    ret.alignment.reserve(std::max(a.size(), b.size()));
    ret.distance = kaldi::LevenshteinAlignment(a, b, eps, &ret.alignment);
    return ret;
}


PYBIND11_MODULE(kaldi_edit_distance, m) {
    m.doc() = "python wrapper of kaldi edit-distance-inl.h";
    py::class_<ErrorStats>(m, "ErrorStats", "error stats in Levelshtein edit distance")
        .def(py::init<>())
        .def_readwrite("ins_num", &ErrorStats::ins)
        .def_readwrite("del_num", &ErrorStats::del)
        .def_readwrite("sub_num", &ErrorStats::sub)
        .def_readwrite("distance", &ErrorStats::total)
        .def_readwrite("ref_num", &ErrorStats::ref)
        .def("__repr__", &ErrorStats::to_string)
        .def("__add__", &ErrorStats::add);

    m.def("edit_distance", edit_distance<std::int64_t>, "Levelshtein edit distance between hyp and ref",
          py::arg("ref"), py::arg("hyp"));

    m.def("edit_distance", edit_distance<std::string>, "Levelshtein edit distance between hyp and ref",
          py::arg("ref"), py::arg("hyp"));

    m.def("align", align<std::int64_t>, "Levelshtein alignment between hyp and ref",
          py::arg("a"), py::arg("b"), py::arg("eps"));

    m.def("align", align<std::string>, "Levelshtein alignment between hyp and ref",
          py::arg("a"), py::arg("b"), py::arg("eps"));

    py::class_<Alignment<std::int64_t>>(m, "IntAlignment", "alignment in Levelshtein edit distance")
        .def(py::init<>())
        .def_readwrite("alignment", &Alignment<std::int64_t>::alignment)
        .def_readwrite("eps", &Alignment<std::int64_t>::eps);


    py::class_<Alignment<std::string>>(m, "StrAlignment", "alignment in Levelshtein edit distance")
        .def(py::init<>())
        .def_readwrite("alignment", &Alignment<std::string>::alignment)
        .def_readwrite("eps", &Alignment<std::string>::eps);
}
