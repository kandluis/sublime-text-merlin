# Merlin 2 for Sublime Text 3

This fork of Sublime-Text-Merlin brings support for Merlin 2. It should be considered alpha quality.
 
## About

This plugin for Sublime Text 3 allows you to analyse OCaml source code, autocomplete and infer types while writing. It checks automatically for syntax or typing errors.

## Installation

First of all, be sure to have [merlin](https://github.com/the-lambda-church/merlin) installed.

The shorter way of doing this is with [opam](opam.ocaml.org), an OCaml package manager:

    opam install merlin

Next, install this package in your *Packages* folder :

    git clone https://github.com/Cynddl/sublime-text-merlin.git

For the moment (during development), sublime-text-merlin is not listed in the Package Manager.

## Work in Progress

This is an initial port of the vim plugin of merlin. Buffers can be synchronised with merlin, but any edit need a full refresh between ST and merlin. Projects are not supported.

If you want to use fully merlin with Sublime Text, fork this repository.


## License

Sublime-Text-Merlin is licensed under the MIT License. See the file LICENSE.md for more details.
