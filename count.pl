use Data::Dumper;

my %counts = {};

while (<STDIN>) {
    # print $_;
    $key = $_;
    chomp $key;
    $counts{$key}++;
}

@keylist = sort(keys(%counts));
    
foreach $key (@keylist) {
    print $counts{$key}."\t$key\n";
}
# print Dumper(\%counts);
