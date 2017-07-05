=pod

=head1 NAME

Error:Message - exception module to handles error messages

=head1 SYNOPSIS

    try
    {
        ...
        throw Error:Message("The message!", "additional message.");
        ...
    }
    catch Error::Message with
    {
        my $except = shift;
        print $except->text();
        print $except->extraText();
    }
    otherwise
    {
        ...
    };

=head1 REQUIRES

Perl5, Error

=head1 DESCRIPTION

This module is used to handles error messages.

=cut

package Error::Message;


use strict;
use Carp qw (cluck confess croak);
use warnings;

use Error qw(:try);
use base qw(Error);




# Package subs
###############

=pod

=head1 STATIC METHODS

=head2 CONSTRUCTOR

B<Description>: Creates a new instance.

B<ArgsCount>: 0-2

=over 4

=item message: (string) (U)

error message.

=item message: (string) (U)

another message if needed.

=back

B<Return>: Error::Message

a new instance.

B<Caller>: Error 'throw' method

B<Exception>:

=cut

sub new
{
    my ($proto, $text, $more_text) = @_;

    $text .= '';
    my (@args) = ();
    local $Error::Depth = $Error::Depth + 1;
    @args = (-file => $1, -line => $2) if ($text =~ s/\s+at\s+(\S+)\s+line\s+(\d+)(?:,\s*<[^>]*>\s+line\s+\d+)?\.?\n?$//s);
    
    my $class = ref($proto) || $proto;

    # instance creation
    my $self = $class->SUPER::new(-text => $text, @args);
    $self->{EXTRA_TEXT} = $more_text;

    return $self;
}




=pod

=head1 ACCESSORS

=cut

=pod

=head2 extraText

B<Description>: returns the additional text given to the exception.

B<ArgsCount>: 0

B<Return>: (string)

the additional text if some, undef otherwise.

B<Example>:

    my $more_text = $exception->extraText();

=cut

sub extraText
{
    my ($self) = @_;
    # check parameters
    if ((1 != @_) || (not ref($self)))
    {
        confess "usage: my \$value = \$instance->extraText();";
    }
    return $self->{EXTRA_TEXT};
}


=pod

=head1 AUTHORS

Alexis DEREEPER (INRA), alexis.dereeper@supagro.inra.fr

=head1 VERSION

Date 10/12/2009

=head1 SEE ALSO

L<Error>

=cut

return 1; # package return
